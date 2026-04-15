import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from parser import extract_text
from analyzer import analyze_resume

load_dotenv()

app = Flask(__name__)

# Allow requests from the React dev server (Vite default: 5173)
CORS(app, origins=["http://localhost:5173", "http://localhost:3000"])

MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}


# ── Health check ──────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# ── Main analyze endpoint ─────────────────────────────────────────────────────

@app.route("/api/analyze", methods=["POST"])
def analyze():
    # 1. Validate file presence
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded. Send a multipart/form-data request with key 'resume'."}), 400

    file = request.files["resume"]

    if not file.filename:
        return jsonify({"error": "Uploaded file has no filename."}), 400

    # 2. Validate extension
    from pathlib import Path
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return jsonify({
            "error": f"Unsupported file type '{suffix}'. Please upload a PDF, DOCX, or TXT file."
        }), 400

    # 3. Read and size-check
    file_bytes = file.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        return jsonify({
            "error": f"File too large. Maximum allowed size is {MAX_FILE_SIZE_MB} MB."
        }), 413

    # 4. Optional job description from form field
    job_description = request.form.get("job_description", "").strip() or None

    # 5. Extract text
    try:
        resume_text = extract_text(file_bytes, file.filename)
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except ImportError as e:
        return jsonify({"error": f"Server dependency missing: {e}"}), 500

    if len(resume_text.strip()) < 50:
        return jsonify({
            "error": "Extracted text is too short. The file may be empty or unreadable."
        }), 422

    # 6. Analyze with Claude
    try:
        feedback = analyze_resume(resume_text, job_description)
    except ValueError as e:
        return jsonify({"error": f"Analysis failed: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error during analysis: {e}"}), 500

    # 7. Return structured result
    return jsonify(feedback.model_dump()), 200


# ── Error handlers ────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found."}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed."}), 405

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error."}), 500


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is not set. Add it to your .env file.")
    
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("FLASK_ENV", "development") == "development"
    
    print(f"🚀 Resume Analyzer backend running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)