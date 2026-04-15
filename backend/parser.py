import io
from pathlib import Path


def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Extract plain text from a PDF or DOCX file.
    Returns the extracted text as a string.
    Raises ValueError for unsupported file types.
    """
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        return _extract_from_pdf(file_bytes)
    elif suffix in (".docx", ".doc"):
        return _extract_from_docx(file_bytes)
    elif suffix == ".txt":
        return file_bytes.decode("utf-8", errors="ignore")
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Please upload a PDF, DOCX, or TXT file.")


def _extract_from_pdf(file_bytes: bytes) -> str:
    try:
        import pypdf
    except ImportError:
        raise ImportError("pypdf is not installed. Run: pip install pypdf")

    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    text_parts = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text.strip())

    full_text = "\n\n".join(text_parts)

    if not full_text.strip():
        raise ValueError(
            "Could not extract text from this PDF. "
            "It may be a scanned image. Please use a text-based PDF."
        )

    return full_text


def _extract_from_docx(file_bytes: bytes) -> str:
    try:
        import docx
    except ImportError:
        raise ImportError("python-docx is not installed. Run: pip install python-docx")

    document = docx.Document(io.BytesIO(file_bytes))
    paragraphs = [para.text.strip() for para in document.paragraphs if para.text.strip()]
    full_text = "\n".join(paragraphs)

    if not full_text.strip():
        raise ValueError("Could not extract text from this DOCX file. The document appears to be empty.")

    return full_text