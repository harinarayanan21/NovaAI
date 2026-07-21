import logging
from typing import Optional
from backend.config.settings import settings
from backend.voice.speech_to_text import stt_service
from backend.voice.text_to_speech import tts_service
from backend.services.groq_service import groq_service
from backend.services.conversation_service import conversation_service
from backend.memory.memory_manager import memory_manager
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class VoiceManager:
    """Orchestrates the full voice pipeline: STT -> Memory -> Groq -> TTS."""

    async def process_voice_chat(
        self,
        audio_data: bytes,
        filename: str,
        user_id: str,
        conversation_id: Optional[int],
        db: AsyncSession,
        language: Optional[str] = None,
        tts_voice: Optional[str] = None,
        tts_rate: Optional[str] = None,
        auto_play: bool = True,
    ) -> dict:
        """Full voice chat pipeline.

        1. Transcribe audio (STT)
        2. Process through memory + Groq
        3. Generate speech (TTS)
        4. Return text + audio
        """
        # Step 1: Transcribe audio
        logger.info("Voice chat from user %s", user_id)
        transcription = await stt_service.transcribe_file(
            file_content=audio_data,
            filename=filename,
            language=language,
        )
        user_text = transcription["text"]
        if not user_text.strip():
            return {
                "transcription": transcription,
                "response_text": "",
                "response_audio": None,
                "conversation_id": conversation_id,
                "error": "No speech detected in audio.",
            }

        # Step 2: Process through the same pipeline as text chat
        # Create or get conversation
        if conversation_id:
            conv = await conversation_service.get_conversation(
                db, conversation_id, user_id
            )
            if not conv:
                title = await conversation_service.generate_title_from_message(user_text)
                conv = await conversation_service.create_conversation(db, user_id, title)
            actual_conversation_id = conv.id
        else:
            title = await conversation_service.generate_title_from_message(user_text)
            conv = await conversation_service.create_conversation(db, user_id, title)
            actual_conversation_id = conv.id

        # Save user message
        await conversation_service.add_message(
            db, actual_conversation_id, "user", user_text
        )

        # Build history
        messages = await conversation_service.get_messages(
            db, actual_conversation_id, user_id
        )
        history = (
            [{"role": m.role, "content": m.content} for m in messages[:-1]]
            if messages
            else []
        )

        # Build memory-enriched context
        context = await memory_manager.build_context(
            user_id=user_id,
            conversation_id=actual_conversation_id,
            current_message=user_text,
            recent_messages=history,
        )

        # Build system prompt with memories
        system_prompt = await memory_manager.build_system_prompt(context)

        # Get AI response
        ai_response = await groq_service.chat(
            user_text,
            history=context.get("recent_messages", history) or history,
            system_prompt=system_prompt,
        )

        # Save AI response
        await conversation_service.add_message(
            db, actual_conversation_id, "assistant", ai_response
        )

        # Process messages for memory extraction
        await memory_manager.process_message(
            user_id, actual_conversation_id, "user", user_text
        )
        await memory_manager.process_message(
            user_id, actual_conversation_id, "assistant", ai_response
        )

        # Step 3: Generate speech
        response_audio = None
        if auto_play:
            try:
                response_audio = await tts_service.synthesize(
                    text=ai_response,
                    voice=tts_voice,
                    rate=tts_rate,
                )
            except Exception as e:
                logger.warning("TTS failed (returning text only): %s", str(e))

        return {
            "transcription": transcription,
            "response_text": ai_response,
            "response_audio": response_audio,
            "conversation_id": actual_conversation_id,
        }


voice_manager = VoiceManager()
