from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.models.conversation import Conversation
from backend.models.message import Message


class ConversationService:
    """Service for conversation and message CRUD."""

    async def create_conversation(
        self, db: AsyncSession, user_id: int, title: str = "New Chat"
    ) -> Conversation:
        conv = Conversation(user_id=user_id, title=title)
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        return conv

    async def get_user_conversations(
        self, db: AsyncSession, user_id: int
    ) -> list[Conversation]:
        result = await db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_conversation(
        self, db: AsyncSession, conversation_id: int, user_id: int
    ) -> Optional[Conversation]:
        result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .options(selectinload(Conversation.messages))
        )
        return result.scalar_one_or_none()

    async def update_conversation_title(
        self, db: AsyncSession, conversation_id: int, user_id: int, title: str
    ) -> Optional[Conversation]:
        conv = await self.get_conversation(db, conversation_id, user_id)
        if not conv:
            return None
        conv.title = title
        conv.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(conv)
        return conv

    async def delete_conversation(
        self, db: AsyncSession, conversation_id: int, user_id: int
    ) -> bool:
        conv = await self.get_conversation(db, conversation_id, user_id)
        if not conv:
            return False
        await db.delete(conv)
        await db.commit()
        return True

    async def get_messages(
        self, db: AsyncSession, conversation_id: int, user_id: int
    ) -> Optional[list[Message]]:
        conv = await self.get_conversation(db, conversation_id, user_id)
        if not conv:
            return None
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        return list(result.scalars().all())

    async def add_message(
        self, db: AsyncSession, conversation_id: int, role: str, content: str
    ) -> Message:
        msg = Message(conversation_id=conversation_id, role=role, content=content)
        db.add(msg)
        # Update conversation timestamp
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conv = result.scalar_one()
        conv.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(msg)
        return msg

    async def generate_title_from_message(self, content: str) -> str:
        """Generate a short title from the first user message."""
        if len(content) <= 50:
            return content
        return content[:50].rsplit(" ", 1)[0] + "..."


conversation_service = ConversationService()
