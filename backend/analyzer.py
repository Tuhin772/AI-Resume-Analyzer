import json
import os
import anthropic
from models import FeedbackResponse, ImprovementItem

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """You are an expert resume reviewer and career coach with 15+ years of experience 
in hiring, recruiting, and talent acquisition across tech, finance, and other industries.

Your job is to analyze resumes and provide structured, actionable feedback. 
You are honest but constructive — your goal is to help the candidate land interviews.

You must respond ONLY with a valid JSON object that matches this exact schema:
{
  "overall_score": <integer 0-100>,
  "summary": "<2-3 sentence overall assessment>",
  "strengths": ["<strength 1>", "<strength 2>", ...],
  "improvements": [
    {
      "section": "<section name>",
      "issue": "<what is wrong>",
      "suggestion": "<concrete fix>"
    }
  ],
  "keywords_found": ["<keyword>", ...],
  "keywords_missing": ["<keyword>", ...],
  "ats_score": <integer 0-100>,
  "ats_notes": "<short note on ATS compatibility>"
}

Scoring guide:
- overall_score 90-100: Exceptional, ready to send
- overall_score 70-89: Good, minor tweaks needed
- overall_score 50-69: Average, significant improvements needed
- overall_score below 50: Needs major rework

Always provide 3-5 strengths, 3-6 improvements, and realistic keyword lists.
Do not include any text outside the JSON object. No markdown, no explanation."""


def analyze_resume(resume_text: str, job_description: str | None = None) -> FeedbackResponse:
    """
    Send resume text to Claude and return structured feedback.
    Optionally accepts a job description to tailor the analysis.
    """
    user_content = _build_user_message(resume_text, job_description)

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_content}
        ]
    )

    raw_text = message.content[0].text.strip()

    return _parse_response(raw_text)


def _build_user_message(resume_text: str, job_description: str | None) -> str:
    parts = ["Please analyze the following resume:\n\n"]
    parts.append("---RESUME START---\n")
    parts.append(resume_text[:8000])  # cap to avoid exceeding context
    parts.append("\n---RESUME END---")

    if job_description and job_description.strip():
        parts.append("\n\n---JOB DESCRIPTION START---\n")
        parts.append(job_description.strip()[:3000])
        parts.append("\n---JOB DESCRIPTION END---")
        parts.append(
            "\n\nPlease tailor your keyword analysis and suggestions specifically "
            "to match the requirements of this job description."
        )

    return "".join(parts)


def _parse_response(raw_text: str) -> FeedbackResponse:
    """Parse Claude's JSON response into a FeedbackResponse model."""
    # Strip any accidental markdown fences just in case
    if raw_text.startswith("```"):
        lines = raw_text.splitlines()
        raw_text = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        )

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned invalid JSON: {e}\nRaw response: {raw_text[:300]}")

    # Coerce improvements into ImprovementItem objects
    improvements = [
        ImprovementItem(**item) if isinstance(item, dict) else item
        for item in data.get("improvements", [])
    ]
    data["improvements"] = improvements

    return FeedbackResponse(**data)