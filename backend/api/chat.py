from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.schemas import ChatRequest, ChatResponse
from backend.services.groq_service import groq_service
from backend.services.conversation_service import conversation_service
from backend.memory.memory_manager import memory_manager
from backend.auth.jwt import get_current_user
from backend.models.user import User
from backend.database.session import get_db
from backend.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Handle chat messages and return AI response. Requires authentication."""
    try:
        logger.info("Message from %s: %s", current_user.username, request.message[:100])

        # Create or get conversation
        if request.conversation_id:
            conv = await conversation_service.get_conversation(
                db, request.conversation_id, current_user.id
            )
            if not conv:
                raise HTTPException(status_code=404, detail="Conversation not found.")
            conversation_id = conv.id
        else:
            title = await conversation_service.generate_title_from_message(
                request.message
            )
            conv = await conversation_service.create_conversation(
                db, current_user.id, title
            )
            conversation_id = conv.id

        # Save user message to SQLite
        await conversation_service.add_message(db, conversation_id, "user", request.message)

        # Build history from SQLite
        messages = await conversation_service.get_messages(db, conversation_id, current_user.id)
        history = [{"role": m.role, "content": m.content} for m in messages[:-1]] if messages else []

        # Build memory-enriched context (Redis + ChromaDB)
        context = await memory_manager.build_context(
            user_id=str(current_user.id),
            conversation_id=conversation_id,
            current_message=request.message,
            recent_messages=history,
        )

        # Build system prompt with memories
        system_prompt = await memory_manager.build_system_prompt(context)

        # Get AI response with memory-enriched context
        ai_response = await groq_service.chat(
            request.message,
            history=context.get("recent_messages", history) or history,
            system_prompt=system_prompt,
        )

        # Save AI response to SQLite
        await conversation_service.add_message(db, conversation_id, "assistant", ai_response)

        # Process messages for memory extraction (Redis + ChromaDB)
        await memory_manager.process_message(
            str(current_user.id), conversation_id, "user", request.message
        )
        await memory_manager.process_message(
            str(current_user.id), conversation_id, "assistant", ai_response
        )

        return ChatResponse(response=ai_response, conversation_id=conversation_id)
    except HTTPException:
        raise
    except ValueError as e:
        logger.error("Configuration error: %s", str(e))
        raise HTTPException(status_code=500, detail="Server configuration error.")
    except Exception as e:
        logger.error("Chat error: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to generate response.")
