import io
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from backend.vision.image_processor import image_processor
from backend.vision.ocr_service import ocr_service
from backend.analytics.metrics import metrics

logger = logging.getLogger(__name__)


class VisionService:
    """Vision service: captioning, VQA, chart/UI analysis, image storage."""

    async def caption(self, image_content: bytes) -> dict:
        """Generate a caption/description for an image."""
        b64 = await image_processor.to_base64(image_content)
        prompt = (
            "Describe this image in detail. Include: main subjects, colors, "
            "composition, text visible, and any notable elements. "
            "Return as JSON: {\"description\": \"...\", \"objects\": [...], \"scene\": \"...\"}"
        )
        result = await self._vision_chat(b64, prompt)
        parsed = self._try_parse_json(result)
        return {
            "description": parsed.get("description", result),
            "objects": parsed.get("objects", []),
            "scene": parsed.get("scene", ""),
            "raw": result,
        }

    async def answer_question(self, image_content: bytes, question: str) -> dict:
        """Answer a question about an image (VQA)."""
        b64 = await image_processor.to_base64(image_content)
        prompt = (
            f"Answer this question about the image: {question}\n\n"
            "Be specific and detailed. If the answer is not visible, say so. "
            "Return as JSON: {\"answer\": \"...\", \"confidence\": \"high|medium|low\", \"reasoning\": \"...\"}"
        )
        result = await self._vision_chat(b64, prompt)
        parsed = self._try_parse_json(result)
        return {
            "answer": parsed.get("answer", result),
            "confidence": parsed.get("confidence", "medium"),
            "reasoning": parsed.get("reasoning", ""),
            "question": question,
        }

    async def explain_chart(self, image_content: bytes) -> dict:
        """Analyze and summarize a chart or visualization."""
        b64 = await image_processor.to_base64(image_content)
        prompt = (
            "Analyze this chart/visualization. Identify: chart type (bar, pie, line, etc.), "
            "key data points, trends, comparisons, and summary. "
            "Return as JSON: {\"chart_type\": \"...\", \"summary\": \"...\", "
            "\"key_insights\": [...], \"data_points\": [{\"label\": \"...\", \"value\": \"...\"}]}"
        )
        result = await self._vision_chat(b64, prompt)
        parsed = self._try_parse_json(result)
        return {
            "chart_type": parsed.get("chart_type", "unknown"),
            "summary": parsed.get("summary", result),
            "key_insights": parsed.get("key_insights", []),
            "data_points": parsed.get("data_points", []),
        }

    async def analyze_ui(self, image_content: bytes) -> dict:
        """Analyze a UI screenshot for issues and suggestions."""
        b64 = await image_processor.to_base64(image_content)
        prompt = (
            "Analyze this UI/screenshot for issues. Look for: layout problems, "
            "broken elements, alignment issues, missing content, error messages, "
            "accessibility problems. "
            "Return as JSON: {\"observations\": [...], \"possible_issues\": [...], "
            "\"suggestions\": [...], \"overall_assessment\": \"...\"}"
        )
        result = await self._vision_chat(b64, prompt)
        parsed = self._try_parse_json(result)
        return {
            "observations": parsed.get("observations", []),
            "possible_issues": parsed.get("possible_issues", []),
            "suggestions": parsed.get("suggestions", []),
            "overall_assessment": parsed.get("overall_assessment", result),
        }

    async def ocr(self, image_content: bytes, filename: str = "") -> dict:
        """Extract text from image using OCR."""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext == "pdf":
            return await ocr_service.extract_from_pdf(image_content)
        return await ocr_service.extract_text(image_content)

    async def full_analysis(self, image_content: bytes, filename: str = "") -> dict:
        """Run all analyses on an image."""
        import time
        t0 = time.perf_counter()

        meta = await image_processor.extract_metadata(image_content)
        ocr_result = await self.ocr(image_content, filename)
        caption_result = await self.caption(image_content)

        elapsed = round((time.perf_counter() - t0) * 1000, 2)
        metrics.increment("vision_requests")
        metrics.record_latency("vision_analysis", elapsed)

        return {
            "metadata": meta,
            "ocr": ocr_result,
            "caption": caption_result,
            "analysis_time_ms": elapsed,
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

    def _try_parse_json(self, text: str) -> dict:
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            try:
                start = text.index("{")
                end = text.rindex("}") + 1
                return json.loads(text[start:end])
            except (ValueError, json.JSONDecodeError):
                return {}


vision_service = VisionService()
