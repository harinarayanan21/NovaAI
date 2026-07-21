import base64
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from backend.auth.jwt import get_current_user
from backend.models.user import User
from backend.database.session import get_db
from backend.voice.speech_to_text import stt_service
from backend.voice.text_to_speech import tts_service
from backend.voice.voice_manager import voice_manager
from backend.utils.logger import logger

router = APIRouter(prefix="/voice", tags=["voice"])


class TranscribeRequest(BaseModel):
    """Base64-encoded audio transcription request."""
    audio: str = Field(..., description="Base64-encoded audio data")
    filename: str = Field(default="audio.wav", description="Audio filename")
    language: Optional[str] = Field(None, description="Language code (e.g., 'en')")


class SpeakRequest(BaseModel):
    """Text-to-speech request."""
    text: str = Field(..., min_length=1, max_length=5000)
    voice: Optional[str] = None
    rate: Optional[str] = None
    volume: Optional[str] = None


class VoiceChatRequest(BaseModel):
    """Full voice chat request with base64 audio."""
    audio: str = Field(..., description="Base64-encoded audio data")
    filename: str = Field(default="audio.wav")
    language: Optional[str] = None
    conversation_id: Optional[int] = None
    voice: Optional[str] = None
    rate: Optional[str] = None
    auto_play: bool = True


class VoiceSettingsResponse(BaseModel):
    """Voice settings response."""
    stt_model: str
    stt_device: str
    stt_language: str
    tts_voice: str
    tts_rate: str
    tts_volume: str
    available_voices: list[dict]
    voice_enabled: bool
    max_audio_size_mb: int
    max_audio_duration_sec: int


@router.post("/transcribe")
async def transcribe_audio(
    request: TranscribeRequest,
    current_user: User = Depends(get_current_user),
):
    """Transcribe audio to text using Faster-Whisper."""
    try:
        audio_data = base64.b64decode(request.audio)
        result = await stt_service.transcribe_file(
            file_content=audio_data,
            filename=request.filename,
            language=request.language,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Transcription error: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to transcribe audio.")


@router.post("/speak")
async def text_to_speech(
    request: SpeakRequest,
    current_user: User = Depends(get_current_user),
):
    """Convert text to speech using Edge TTS. Returns base64-encoded audio."""
    try:
        audio_bytes = await tts_service.synthesize(
            text=request.text,
            voice=request.voice,
            rate=request.rate,
            volume=request.volume,
        )
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return {
            "audio": audio_b64,
            "format": "mp3",
            "size_bytes": len(audio_bytes),
        }
    except Exception as e:
        logger.error("TTS error: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to generate speech.")


@router.post("/chat")
async def voice_chat(
    request: VoiceChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Full voice chat: transcribe audio, process with Groq, return text + audio."""
    try:
        audio_data = base64.b64decode(request.audio)
        result = await voice_manager.process_voice_chat(
            audio_data=audio_data,
            filename=request.filename,
            user_id=str(current_user.id),
            conversation_id=request.conversation_id,
            db=db,
            language=request.language,
            tts_voice=request.voice,
            tts_rate=request.rate,
            auto_play=request.auto_play,
        )

        response = {
            "transcription": result["transcription"],
            "response_text": result["response_text"],
            "conversation_id": result["conversation_id"],
        }

        if result.get("response_audio"):
            response["response_audio"] = base64.b64encode(
                result["response_audio"]
            ).decode("utf-8")
            response["audio_format"] = "mp3"

        if result.get("error"):
            response["error"] = result["error"]

        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Voice chat error: %s", str(e))
        raise HTTPException(status_code=500, detail="Voice chat failed.")


@router.post("/chat/upload")
async def voice_chat_upload(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    conversation_id: Optional[int] = Form(None),
    voice: Optional[str] = Form(None),
    rate: Optional[str] = Form(None),
    auto_play: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Voice chat via file upload instead of base64."""
    try:
        content = await file.read()
        result = await voice_manager.process_voice_chat(
            audio_data=content,
            filename=file.filename or "audio.wav",
            user_id=str(current_user.id),
            conversation_id=conversation_id,
            db=db,
            language=language,
            tts_voice=voice,
            tts_rate=rate,
            auto_play=auto_play,
        )

        response = {
            "transcription": result["transcription"],
            "response_text": result["response_text"],
            "conversation_id": result["conversation_id"],
        }

        if result.get("response_audio"):
            response["response_audio"] = base64.b64encode(
                result["response_audio"]
            ).decode("utf-8")
            response["audio_format"] = "mp3"

        if result.get("error"):
            response["error"] = result["error"]

        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Voice chat upload error: %s", str(e))
        raise HTTPException(status_code=500, detail="Voice chat failed.")


@router.get("/settings", response_model=VoiceSettingsResponse)
async def get_voice_settings(
    current_user: User = Depends(get_current_user),
):
    """Get current voice settings and available voices."""
    try:
        from backend.config.settings import settings
        voices = await tts_service.get_voices()
        return VoiceSettingsResponse(
            stt_model=settings.WHISPER_MODEL,
            stt_device=settings.WHISPER_DEVICE,
            stt_language=settings.WHISPER_LANGUAGE,
            tts_voice=settings.TTS_VOICE,
            tts_rate=settings.TTS_RATE,
            tts_volume=settings.TTS_VOLUME,
            available_voices=voices[:50],
            voice_enabled=settings.VOICE_ENABLED,
            max_audio_size_mb=settings.MAX_AUDIO_SIZE_MB,
            max_audio_duration_sec=settings.MAX_AUDIO_DURATION_SEC,
        )
    except Exception as e:
        logger.error("Voice settings error: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to get voice settings.")


@router.get("/voices")
async def list_voices(
    language: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """List available TTS voices."""
    try:
        voices = await tts_service.get_voices(language=language)
        return {"voices": voices}
    except Exception as e:
        logger.error("List voices error: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to list voices.")


@router.get("/status")
async def voice_status(
    current_user: User = Depends(get_current_user),
):
    """Check voice service status."""
    stt_ok = await stt_service.ping()
    tts_ok = await tts_service.ping()
    return {
        "stt_available": stt_ok,
        "tts_available": tts_ok,
        "stt_model": "faster-whisper" if stt_ok else "unavailable",
        "tts_engine": "edge-tts" if tts_ok else "unavailable",
    }
