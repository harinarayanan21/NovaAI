import io
import logging
from typing import Optional
import httpx
from backend.config.settings import settings

logger = logging.getLogger(__name__)

GROQ_STT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


class SpeechToTextService:
    """Speech-to-text service using Groq Whisper API."""

    def __init__(self):
        self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        filename: str = "audio.wav",
    ) -> dict:
        """Transcribe audio data to text using Groq Whisper API.

        Args:
            audio_data: Raw audio bytes (WAV, MP3, WEBM, etc.)
            language: Language code (e.g., 'en', 'es'). None for auto-detect.
            filename: Original filename (used for format detection)

        Returns:
            dict with keys: text, language, segments, duration
        """
        try:
            if not settings.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY is not set.")

            # Determine content type from filename
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "wav"
            content_type_map = {
                "wav": "audio/wav",
                "mp3": "audio/mpeg",
                "webm": "audio/webm",
                "ogg": "audio/ogg",
                "flac": "audio/flac",
                "m4a": "audio/mp4",
                "mp4": "audio/mp4",
            }
            content_type = content_type_map.get(ext, "audio/wav")

            # Build multipart form data
            files = {
                "file": (filename, audio_data, content_type),
            }
            data = {
                "model": "whisper-large-v3",
                "response_format": "verbose_json",
            }
            if language and language != "auto":
                data["language"] = language

            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            }

            client = self._get_client()
            response = await client.post(
                GROQ_STT_URL,
                headers=headers,
                files=files,
                data=data,
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error("Groq STT error %d: %s", response.status_code, error_detail)
                raise ValueError(f"Transcription failed: {error_detail}")

            result = response.json()

            # Parse the response
            text = result.get("text", "")
            lang = result.get("language", language or "en")
            duration = result.get("duration", 0)

            # Build segments from words if available
            segments = []
            if "segments" in result:
                for seg in result["segments"]:
                    segments.append({
                        "start": round(seg.get("start", 0), 2),
                        "end": round(seg.get("end", 0), 2),
                        "text": seg.get("text", "").strip(),
                    })

            logger.info(
                "Transcribed via Groq: lang=%s, duration=%.1fs, text=%s",
                lang,
                duration,
                text[:100],
            )

            return {
                "text": text.strip(),
                "language": lang,
                "language_probability": 1.0,
                "duration": round(duration, 2),
                "segments": segments,
            }

        except ValueError:
            raise
        except Exception as e:
            logger.error("Transcription error: %s", str(e))
            raise

    async def transcribe_file(
        self,
        file_content: bytes,
        filename: str,
        language: Optional[str] = None,
    ) -> dict:
        """Transcribe an uploaded audio file."""
        max_bytes = settings.MAX_AUDIO_SIZE_MB * 1024 * 1024
        if len(file_content) > max_bytes:
            raise ValueError(
                f"Audio file too large. Max size: {settings.MAX_AUDIO_SIZE_MB}MB"
            )

        return await self.transcribe(
            audio_data=file_content,
            language=language,
            filename=filename,
        )

    async def ping(self) -> bool:
        """Check if the STT service is available."""
        return bool(settings.GROQ_API_KEY)

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


stt_service = SpeechToTextService()
