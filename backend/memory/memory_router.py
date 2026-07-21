from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from backend.auth.jwt import get_current_user
from backend.models.user import User
from backend.memory.memory_manager import memory_manager

router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryResponse(BaseModel):
    id: str
    content: str
    metadata: dict
    similarity: Optional[float] = None


class MemorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    category: Optional[str] = None


class MemoryStatsResponse(BaseModel):
    total: int
    categories: dict
    redis_available: bool
    redis_fallback: bool
    chromadb_available: bool
    embedding_model: str


@router.get("", response_model=list[MemoryResponse])
async def list_memories(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """List all memories for the current user."""
    memories = await memory_manager.get_memories(str(current_user.id), category=category)
    return [MemoryResponse(id=m["id"], content=m["content"], metadata=m["metadata"]) for m in memories]


@router.get("/stats", response_model=MemoryStatsResponse)
async def get_memory_stats(
    current_user: User = Depends(get_current_user),
):
    """Get memory statistics for the current user."""
    stats = await memory_manager.get_stats(str(current_user.id))
    return MemoryStatsResponse(**stats)


@router.post("/search", response_model=list[MemoryResponse])
async def search_memories(
    request: MemorySearchRequest,
    current_user: User = Depends(get_current_user),
):
    """Search memories by semantic similarity."""
    memories = await memory_manager.search(
        str(current_user.id), request.query, category=request.category
    )
    return [
        MemoryResponse(
            id=m["id"],
            content=m["content"],
            metadata=m["metadata"],
            similarity=m["similarity"],
        )
        for m in memories
    ]


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a specific memory."""
    deleted = await memory_manager.delete_memory(str(current_user.id), memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found.")
    return {"detail": "Memory deleted."}


@router.delete("")
async def clear_all_memories(
    current_user: User = Depends(get_current_user),
):
    """Clear all memories for the current user."""
    await memory_manager.clear_user_memories(str(current_user.id))
    return {"detail": "All memories cleared."}
