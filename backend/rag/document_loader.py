import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SUPPORTED_TYPES = {"pdf", "docx", "txt", "md"}


def load_document(content: bytes, filename: str) -> str:
    """Extract text from a document based on its file type.

    Args:
        content: Raw file bytes.
        filename: Original filename (used to determine type).

    Returns:
        Extracted text as a single string.

    Raises:
        ValueError: If the file type is unsupported or extraction fails.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in SUPPORTED_TYPES:
        raise ValueError(
            f"Unsupported file type: '{ext}'. "
            f"Supported types: {', '.join(sorted(SUPPORTED_TYPES))}"
        )

    try:
        if ext == "pdf":
            return _load_pdf(content)
        elif ext == "docx":
            return _load_docx(content)
        else:
            return _load_text(content)
    except ValueError:
        raise
    except Exception as e:
        logger.error("Failed to extract text from %s: %s", filename, str(e))
        raise ValueError(f"Failed to extract text: {str(e)}")


def _load_pdf(content: bytes) -> str:
    """Extract text from a PDF file."""
    from pypdf import PdfReader
    import io

    reader = PdfReader(io.BytesIO(content))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages.append(text.strip())

    if not pages:
        raise ValueError("PDF contains no extractable text.")

    return "\n\n".join(pages)


def _load_docx(content: bytes) -> str:
    """Extract text from a DOCX file."""
    from docx import Document
    import io

    doc = Document(io.BytesIO(content))
    paragraphs = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)

    if not paragraphs:
        raise ValueError("DOCX contains no extractable text.")

    return "\n\n".join(paragraphs)


def _load_text(content: bytes) -> str:
    """Extract text from a plain text file (TXT/MD)."""
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = content.decode("latin-1")
        except UnicodeDecodeError:
            text = content.decode("ascii", errors="replace")

    text = text.strip()
    if not text:
        raise ValueError("File is empty.")

    return text
