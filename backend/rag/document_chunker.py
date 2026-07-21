import re
import logging

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 200


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks, preserving sentence boundaries.

    Args:
        text: The full document text.
        chunk_size: Target chunk size in characters.
        chunk_overlap: Overlap between consecutive chunks in characters.

    Returns:
        List of text chunks.
    """
    if not text or not text.strip():
        return []

    text = _clean_text(text)

    if len(text) <= chunk_size:
        return [text]

    sentences = _split_into_sentences(text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if len(current_chunk) + len(sentence) + 1 <= chunk_size:
            current_chunk = (current_chunk + " " + sentence).strip() if current_chunk else sentence
        else:
            if current_chunk:
                chunks.append(current_chunk)
                overlap_text = _get_overlap_tail(current_chunk, chunk_overlap)
                current_chunk = (overlap_text + " " + sentence).strip() if overlap_text else sentence
            else:
                if len(sentence) > chunk_size:
                    sub_chunks = _force_split(sentence, chunk_size, chunk_overlap)
                    chunks.extend(sub_chunks)
                    if sub_chunks:
                        current_chunk = sub_chunks[-1]
                else:
                    current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk)

    chunks = [c for c in chunks if c.strip()]
    logger.info("Split %d chars into %d chunks", len(text), len(chunks))
    return chunks


def _clean_text(text: str) -> str:
    """Clean extracted text: normalize whitespace, remove artifacts."""
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[^\S\n]+", " ", text)
    return text.strip()


def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentences using punctuation boundaries."""
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\u00C0-\u024F])", text)
    if len(parts) <= 1:
        parts = re.split(r"\n\s*\n", text)
    if len(parts) <= 1:
        parts = re.split(r"\n", text)
    if len(parts) <= 1:
        parts = re.split(r"(?<=\. )", text)
    return [p for p in parts if p.strip()]


def _get_overlap_tail(text: str, overlap: int) -> str:
    """Get the tail of text with approximately 'overlap' characters."""
    if overlap <= 0 or len(text) <= overlap:
        return ""
    tail = text[-overlap:]
    space_idx = tail.find(" ")
    if space_idx >= 0:
        tail = tail[space_idx + 1 :]
    return tail


def _force_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Force-split a long text into fixed-size chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            space_idx = text.rfind(" ", start + chunk_size // 2, end)
            if space_idx > start:
                end = space_idx
        chunks.append(text[start:end].strip())
        start = end - overlap
        if start >= len(text):
            break
    return [c for c in chunks if c]
