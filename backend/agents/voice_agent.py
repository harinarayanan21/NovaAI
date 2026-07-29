import logging
from backend.graph.state import AgentState

logger = logging.getLogger(__name__)


async def voice_agent_node(state: AgentState) -> dict:
    """Voice agent that handles STT and TTS.

    Integrates with existing speech_to_text and text_to_speech services.
    No duplicated code — delegates to existing infrastructure.
    """
    try:
        voice_data = state.get("voice_data")
        if not voice_data:
            logger.info("Voice agent: no voice data in state, skipping")
            return {
                "metadata": {
                    **state.get("metadata", {}),
                    "voice_agent_completed": True,
                    "voice_agent_message": "No voice data",
                },
            }

        from backend.voice.speech_to_text import stt_service
        from backend.voice.text_to_speech import tts_service

        audio_data = voice_data.get("audio_data", b"")
        filename = voice_data.get("filename", "audio.wav")
        language = voice_data.get("language")
        tts_voice = voice_data.get("tts_voice")
        tts_rate = voice_data.get("tts_rate")

        transcription = None
        if audio_data:
            transcription = await stt_service.transcribe_file(
                file_content=audio_data,
                filename=filename,
                language=language,
            )
            logger.info("Voice agent: transcribed '%s'", transcription.get("text", "")[:100])

        tts_audio = None
        response_text = state.get("final_response", "")
        if response_text:
            try:
                tts_audio = await tts_service.synthesize(
                    text=response_text,
                    voice=tts_voice,
                    rate=tts_rate,
                )
                logger.info("Voice agent: synthesized %d bytes of audio", len(tts_audio))
            except Exception as e:
                logger.warning("Voice agent TTS failed: %s", str(e))

        return {
            "metadata": {
                **state.get("metadata", {}),
                "voice_agent_transcription": transcription,
                "voice_agent_tts_audio": tts_audio,
                "voice_agent_completed": True,
            },
        }

    except Exception as e:
        logger.error("Voice agent error: %s", str(e))
        return {
            "metadata": {
                **state.get("metadata", {}),
                "voice_agent_completed": False,
                "voice_agent_error": str(e)[:200],
            },
            "errors": state.get("errors", []) + [f"voice_agent: {str(e)[:200]}"],
        }
