import io
import logging
import time
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field

from backend.auth.jwt import get_current_user
from backend.models.user import User
from backend.vision.vision_service import vision_service
from backend.vision.image_processor import image_processor
from backend.vision.ocr_service import ocr_service
from backend.analytics.metrics import metrics
from backend.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vision", tags=["vision"])


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload an image for processing and storage."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    supported = {"png", "jpg", "jpeg", "webp"}
    if ext not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: '{ext}'. Supported: {', '.join(sorted(supported))}",
        )

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds 20MB limit.")

    validation = await image_processor.validate(content, file.filename)
    if not validation.get("valid"):
        raise HTTPException(status_code=400, detail="; ".join(validation.get("errors", [])))

    saved = await image_processor.save(content, file.filename, current_user.id)
    meta = await image_processor.extract_metadata(content)

    result = await vision_service.full_analysis(content, file.filename)

    metrics.increment("vision_uploads")

    return {
        "filename": file.filename,
        "stored_name": saved["stored_name"],
        "metadata": meta,
        "analysis": result,
    }


@router.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Run full analysis on an image (caption, OCR, metadata)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    content = await file.read()
    validation = await image_processor.validate(content, file.filename)
    if not validation.get("valid"):
        raise HTTPException(status_code=400, detail="; ".join(validation.get("errors", [])))

    result = await vision_service.full_analysis(content, file.filename)
    metrics.increment("vision_requests")
    return result


@router.post("/ocr")
async def ocr_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Extract text from an image or PDF using OCR."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    content = await file.read()
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""

    t0 = time.perf_counter()
    if ext == "pdf":
        result = await ocr_service.extract_from_pdf(content)
    else:
        validation = await image_processor.validate(content, file.filename)
        if not validation.get("valid"):
            raise HTTPException(status_code=400, detail="; ".join(validation.get("errors", [])))
        result = await ocr_service.extract_text(content)

    elapsed = round((time.perf_counter() - t0) * 1000, 2)
    metrics.increment("ocr_requests")
    metrics.record_latency("ocr_latency", elapsed)

    return {
        "filename": file.filename,
        "text": result.get("text", ""),
        "blocks": result.get("blocks", []),
        "total_blocks": result.get("total_blocks", 0),
        "confidence": result.get("confidence", 0),
        "tables": result.get("tables", []),
        "pages": result.get("pages", 1),
        "method": result.get("method", "vision_llm"),
        "processing_time_ms": elapsed,
    }


@router.post("/question")
async def ask_question(
    file: UploadFile = File(...),
    question: str = Form(default="Describe this image."),
    current_user: User = Depends(get_current_user),
):
    """Ask a question about an image (Visual Question Answering)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    content = await file.read()
    validation = await image_processor.validate(content, file.filename)
    if not validation.get("valid"):
        raise HTTPException(status_code=400, detail="; ".join(validation.get("errors", [])))

    t0 = time.perf_counter()
    result = await vision_service.answer_question(content, question)
    elapsed = round((time.perf_counter() - t0) * 1000, 2)

    metrics.increment("vision_requests")
    metrics.record_latency("vqa_latency", elapsed)

    return {
        "question": question,
        "answer": result.get("answer", ""),
        "confidence": result.get("confidence", "medium"),
        "reasoning": result.get("reasoning", ""),
        "processing_time_ms": elapsed,
    }


@router.post("/caption")
async def caption_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Generate a caption/description for an image."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    content = await file.read()
    validation = await image_processor.validate(content, file.filename)
    if not validation.get("valid"):
        raise HTTPException(status_code=400, detail="; ".join(validation.get("errors", [])))

    result = await vision_service.caption(content)
    metrics.increment("vision_requests")
    return result


@router.post("/chart")
async def analyze_chart(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Analyze and summarize a chart or visualization."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    content = await file.read()
    validation = await image_processor.validate(content, file.filename)
    if not validation.get("valid"):
        raise HTTPException(status_code=400, detail="; ".join(validation.get("errors", [])))

    result = await vision_service.explain_chart(content)
    metrics.increment("vision_requests")
    return result


@router.post("/ui-analysis")
async def analyze_ui_screenshot(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Analyze a UI screenshot for issues and suggestions."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    content = await file.read()
    validation = await image_processor.validate(content, file.filename)
    if not validation.get("valid"):
        raise HTTPException(status_code=400, detail="; ".join(validation.get("errors", [])))

    result = await vision_service.analyze_ui(content)
    metrics.increment("vision_requests")
    return result


@router.get("/history")
async def get_vision_history(
    current_user: User = Depends(get_current_user),
):
    """List all uploaded images."""
    from backend.vision.image_knowledge import image_knowledge
    images = await image_knowledge.list_images(current_user.id)
    return {"images": images, "total": len(images)}


@router.delete("/{image_id}")
async def delete_image(
    image_id: int,
    current_user: User = Depends(get_current_user),
):
    """Delete an uploaded image and its embeddings."""
    from backend.vision.image_knowledge import image_knowledge
    deleted = await image_knowledge.delete_image(image_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Image not found.")
    return {"detail": "Image deleted."}


@router.post("/search")
async def search_images(
    query: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    """Semantic search across stored image knowledge."""
    from backend.vision.image_knowledge import image_knowledge
    results = await image_knowledge.search(current_user.id, query)
    return {"results": results, "total": len(results)}
