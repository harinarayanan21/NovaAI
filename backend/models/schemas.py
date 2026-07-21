from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    conversation_id: Optional[int] = Field(None, description="Conversation ID for context-aware chat")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    response: str = Field(..., description="AI assistant response")
    conversation_id: int = Field(..., description="Conversation ID")
