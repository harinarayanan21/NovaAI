import logging
from backend.graph.state import AgentState

logger = logging.getLogger(__name__)


async def vision_agent_node(state: AgentState) -> dict:
    """Vision agent that processes image-related requests.

    Triggered when the supervisor detects vision/image/OCR requests.
    Uses the vision service for image analysis, OCR, chart/UI analysis.
    """
    try:
        user_message = state.get("user_message", "")
        vision_data = state.get("vision_data", {})

        if not vision_data.get("image_content"):
            return {
                "vision_data": {
                    **vision_data,
                    "note": "No image provided. Upload an image first.",
                },
                "metadata": {
                    **state.get("metadata", {}),
                    "vision_agent_completed": True,
                },
            }

        from backend.vision.vision_service import vision_service
        from backend.vision.image_knowledge import image_knowledge

        image_content = vision_data["image_content"]
        filename = vision_data.get("filename", "image.jpg")

        from backend.services.groq_service import groq_service

        system_prompt = (
            "You are a vision analysis assistant. Based on the user's request and the image analysis results, "
            "provide a helpful response. Available analyses: caption (describe image), "
            "ocr (extract text), chart analysis, UI analysis, specific questions about the image. "
            "Respond conversationally."
        )

        analysis = await vision_service.full_analysis(image_content, filename)
        caption = analysis.get("caption", {}).get("description", "")
        ocr_text = analysis.get("ocr", {}).get("text", "")
        meta = analysis.get("metadata", {})

        store_info = {
            "caption": caption,
            "ocr_text": ocr_text,
            "description": caption,
        }

        try:
            await image_knowledge.store_image(
                user_id=int(state.get("user_id", 0)),
                filename=filename,
                stored_name=filename,
                file_type=filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg",
                file_size=len(image_content),
                width=meta.get("width", 0),
                height=meta.get("height", 0),
                **store_info,
            )
        except Exception as e:
            logger.warning("Failed to store image in knowledge base: %s", e)

        context = f"Image analysis results:\nCaption: {caption}\nOCR Text: {ocr_text}\nMetadata: {meta}"

        response = await groq_service._plain_chat(
            user_message,
            history=[{"role": "system", "content": system_prompt + "\n\n" + context}],
            system_prompt=system_prompt + "\n\n" + context,
        )

        return {
            "vision_data": {
                **vision_data,
                "analysis": analysis,
                "caption": caption,
                "ocr_text": ocr_text,
            },
            "metadata": {
                **state.get("metadata", {}),
                "vision_agent_completed": True,
                "vision_analysis_time_ms": analysis.get("analysis_time_ms", 0),
            },
        }

    except Exception as e:
        logger.error("Vision agent error: %s", e)
        return {
            "errors": state.get("errors", []) + [f"vision_agent: {str(e)[:200]}"],
            "metadata": {
                **state.get("metadata", {}),
                "vision_agent_error": str(e)[:200],
            },
        }
