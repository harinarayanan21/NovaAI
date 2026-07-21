from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, Field
from backend.auth.jwt import get_current_user
from backend.models.user import User
from backend.rag.rag_manager import rag_manager
from backend.config.settings import settings

router = APIRouter(prefix="/rag", tags=["rag"])


class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    n_results: int = Field(default=5, ge=1, le=20)


class RAGUploadResponse(BaseModel):
    document_id: int
    filename: str
    chunk_count: int
    total_chars: Optional[int] = None
    status: str
    error: Optional[str] = None


class RAGDocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    chunk_count: int
    status: str
    error_message: Optional[str] = None
    created_at: Optional[str] = None


class RAGQueryResponse(BaseModel):
    answer: str
    sources: list[dict]


class RAGStatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    by_type: dict


@router.post("/upload", response_model=RAGUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload a document for RAG processing (PDF, DOCX, TXT, MD)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    supported = {"pdf", "docx", "txt", "md"}
    if ext not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: '{ext}'. Supported: {', '.join(sorted(supported))}",
        )

    max_bytes = settings.RAG_MAX_FILE_SIZE_MB * 1024 * 1024
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {settings.RAG_MAX_FILE_SIZE_MB}MB",
        )

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty.")

    result = await rag_manager.upload_document(
        user_id=current_user.id,
        filename=file.filename,
        file_content=content,
    )

    if result["status"] == "failed":
        raise HTTPException(status_code=500, detail=result.get("error", "Processing failed"))

    return RAGUploadResponse(**result)


@router.get("/documents", response_model=list[RAGDocumentResponse])
async def list_documents(
    current_user: User = Depends(get_current_user),
):
    """List all uploaded documents for the current user."""
    docs = await rag_manager.list_documents(current_user.id)
    return [RAGDocumentResponse(**d) for d in docs]


@router.delete("/document/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
):
    """Delete a document and all its chunks."""
    deleted = await rag_manager.delete_document(current_user.id, document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"detail": "Document and all chunks deleted."}


@router.post("/query", response_model=RAGQueryResponse)
async def query_documents(
    request: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
):
    """Ask a question about uploaded documents. Uses RAG to find relevant chunks and generate an answer."""
    result = await rag_manager.query(
        user_id=current_user.id,
        question=request.question,
        n_results=request.n_results,
    )
    return RAGQueryResponse(**result)


@router.get("/stats", response_model=RAGStatsResponse)
async def get_rag_stats(
    current_user: User = Depends(get_current_user),
):
    """Get RAG statistics for the current user."""
    stats = await rag_manager.get_stats(current_user.id)
    return RAGStatsResponse(**stats)
