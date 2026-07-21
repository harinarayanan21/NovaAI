from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.schemas.conversation import ConversationCreate, ConversationResponse, ConversationUpdate
from backend.schemas.message import MessageCreate, MessageResponse
from backend.services.conversation_service import conversation_service
from backend.auth.jwt import get_current_user
from backend.models.user import User
from backend.database.session import get_db

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    convs = await conversation_service.get_user_conversations(db, current_user.id)
    return convs


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await conversation_service.create_conversation(db, current_user.id, request.title)
    return conv


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await conversation_service.get_conversation(db, conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conv


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    request: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await conversation_service.update_conversation_title(
        db, conversation_id, current_user.id, request.title
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conv


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await conversation_service.delete_conversation(db, conversation_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"detail": "Conversation deleted."}


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(
    conversation_id: int,
    request: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await conversation_service.get_conversation(db, conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    msg = await conversation_service.add_message(db, conversation_id, "user", request.content)
    return msg


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    msgs = await conversation_service.get_messages(db, conversation_id, current_user.id)
    if msgs is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return msgs
