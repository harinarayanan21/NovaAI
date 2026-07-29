import io
import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class OCRService:
    """OCR service using pytesseract with fallback to vision LLM."""

    def __init__(self):
        self._tesseract_available = None

    def _check_tesseract(self) -> bool:
        if self._tesseract_available is not None:
            return self._tesseract_available
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            self._tesseract_available = True
            logger.info("Tesseract OCR available")
        except Exception as e:
            logger.warning("Tesseract not available: %s", e)
            self._tesseract_available = False
        return self._tesseract_available

    async def extract_text(self, image_content: bytes) -> dict:
        """Extract text from image bytes using OCR.

        Returns structured result with text, blocks, confidence.
        """
        if self._check_tesseract():
            return await self._ocr_with_tesseract(image_content)
        return await self._ocr_with_vision(image_content)

    async def extract_from_pdf(self, pdf_content: bytes) -> dict:
        """Extract text from PDF pages using OCR."""
        try:
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(pdf_content, dpi=200)
        except Exception as e:
            return {"text": "", "pages": 0, "error": f"PDF conversion failed: {str(e)}", "blocks": []}

        all_text = []
        all_blocks = []
        for page_num, img in enumerate(images):
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            result = await self.extract_text(buf.getvalue())
            if result.get("text"):
                all_text.append(f"[Page {page_num + 1}]\n{result['text']}")
            all_blocks.extend(result.get("blocks", []))

        return {
            "text": "\n\n".join(all_text),
            "pages": len(images),
            "blocks": all_blocks,
            "method": "tesseract" if self._check_tesseract() else "vision_llm",
        }

    async def _ocr_with_tesseract(self, image_content: bytes) -> dict:
        import pytesseract
        from PIL import Image

        img = Image.open(io.BytesIO(image_content))
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        text = pytesseract.image_to_string(img).strip()
        confidence_values = [int(c) for c in data.get("conf", []) if c != "-1"]
        avg_confidence = round(sum(confidence_values) / len(confidence_values), 2) if confidence_values else 0

        blocks = []
        n_boxes = len(data.get("level", []))
        for i in range(n_boxes):
            if int(data["conf"][i]) > 30:
                blocks.append({
                    "text": data["text"][i],
                    "confidence": int(data["conf"][i]),
                    "x": data["left"][i],
                    "y": data["top"][i],
                    "w": data["width"][i],
                    "h": data["height"][i],
                })

        blocks = [b for b in blocks if b["text"].strip()]

        tables = self._detect_tables(blocks)

        return {
            "text": text,
            "blocks": blocks,
            "total_blocks": len(blocks),
            "confidence": avg_confidence,
            "tables": tables,
            "method": "tesseract",
        }

    def _detect_tables(self, blocks: list[dict]) -> list[list[dict]]:
        """Simple table detection by grouping blocks by Y-coordinate."""
        if not blocks:
            return []
        rows = {}
        for b in blocks:
            row_key = round(b["y"] / 20)
            if row_key not in rows:
                rows[row_key] = []
            rows[row_key].append(b)
        tables = []
        for row_key in sorted(rows.keys()):
            row = sorted(rows[row_key], key=lambda x: x["x"])
            if len(row) > 1:
                tables.append(row)
        return tables

    async def _ocr_with_vision(self, image_content: bytes) -> dict:
        from backend.vision.image_processor import image_processor
        from backend.services.groq_service import groq_service

        b64 = await image_processor.to_base64(image_content)
        prompt = (
            "Extract all text from this image. Return the exact text content. "
            "If there are tables, format them using markdown table syntax."
        )
        result = await self._vision_chat(b64, prompt)

        return {
            "text": result,
            "blocks": [],
            "total_blocks": 0,
            "confidence": 0,
            "tables": [],
            "method": "vision_llm",
        }

    async def _vision_chat(self, image_base64: str, prompt: str) -> str:
        from backend.services.groq_service import groq_service
        from langchain_core.messages import HumanMessage

        llm = groq_service._get_llm()
        image_url = f"data:image/jpeg;base64,{image_base64}"
        msg = HumanMessage(content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_url}},
        ])
        response = await llm.ainvoke([msg])
        return response.content or ""


ocr_service = OCRService()
