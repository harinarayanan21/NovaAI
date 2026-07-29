import io
import os
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

VALID_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_DIMENSION = 4096


class ImageProcessor:
    """Image validation, preprocessing, and metadata extraction."""

    def __init__(self, upload_dir: str = "uploads/vision"):
        self._upload_dir = Path(upload_dir)

    async def validate(self, content: bytes, filename: str) -> dict:
        """Validate an image file. Returns validation result with metadata."""
        errors = []
        ext = Path(filename).suffix.lower()
        if ext not in VALID_EXTENSIONS:
            errors.append(f"Unsupported format: {ext}. Supported: {', '.join(sorted(VALID_EXTENSIONS))}")

        if len(content) == 0:
            errors.append("File is empty")

        if len(content) > 20 * 1024 * 1024:
            errors.append("File exceeds 20MB limit")

        if errors:
            return {"valid": False, "errors": errors}

        try:
            from PIL import Image
            img = Image.open(io.BytesIO(content))
            img.verify()
            img = Image.open(io.BytesIO(content))
            width, height = img.size
            return {
                "valid": True,
                "format": img.format,
                "mode": img.mode,
                "width": width,
                "height": height,
                "aspect_ratio": round(width / height, 4) if height else 0,
                "file_size": len(content),
            }
        except Exception as e:
            return {"valid": False, "errors": [f"Invalid image: {str(e)}"]}

    async def preprocess(self, content: bytes, max_dim: int = MAX_DIMENSION) -> bytes:
        """Resize image if needed and return processed bytes."""
        from PIL import Image
        img = Image.open(io.BytesIO(content))
        if img.mode == "RGBA":
            img = img.convert("RGB")
        w, h = img.size
        if w > max_dim or h > max_dim:
            ratio = min(max_dim / w, max_dim / h)
            new_w = int(w * ratio)
            new_h = int(h * ratio)
            img = img.resize((new_w, new_h), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()

    async def save(self, content: bytes, filename: str, user_id: int) -> dict:
        """Save image to disk and return file info."""
        self._upload_dir.mkdir(parents=True, exist_ok=True)
        ext = Path(filename).suffix.lower()
        stored_name = f"{uuid.uuid4().hex}{ext}"
        filepath = self._upload_dir / stored_name
        filepath.write_bytes(content)
        return {
            "stored_name": stored_name,
            "filepath": str(filepath),
            "size": len(content),
        }

    async def extract_metadata(self, content: bytes) -> dict:
        """Extract EXIF and other metadata from image."""
        from PIL import Image, ExifTags
        meta = {}
        try:
            img = Image.open(io.BytesIO(content))
            exif = img.getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                    if isinstance(value, (str, int, float)):
                        meta[tag_name] = str(value)[:200]
            meta["format"] = img.format
            meta["mode"] = img.mode
            meta["width"], meta["height"] = img.size
        except Exception as e:
            logger.warning("Metadata extraction failed: %s", e)
        return meta

    async def to_base64(self, content: bytes) -> str:
        """Convert image bytes to base64 string."""
        import base64
        return base64.b64encode(content).decode("utf-8")


image_processor = ImageProcessor()
