import io
import logging
import edge_tts
from typing import Optional
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class TextToSpeechService:
    """Text-to-speech service using Edge TTS."""

    def __init__(self):
        self._voices = None

    async def _get_voices(self) -> list[dict]:
        """Get available voices (cached)."""
        if self._voices is not None:
            return self._voices
        try:
            voices = await edge_tts.list_voices()
            self._voices = voices
            return self._voices
        except Exception as e:
            logger.error("Failed to list voices: %s", str(e))
            return []

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        volume: Optional[str] = None,
    ) -> bytes:
        """Convert text to speech audio.

        Args:
            text: Text to synthesize
            voice: Voice name (e.g., 'en-US-GuyNeural')
            rate: Speaking rate (e.g., '+0%', '+20%', '-10%')
            volume: Volume (e.g., '+0%', '+50%')

        Returns:
            MP3 audio bytes
        """
        try:
            v = voice or settings.TTS_VOICE
            r = rate or settings.TTS_RATE
            vol = volume or settings.TTS_VOLUME

            communicate = edge_tts.Communicate(
                text=text,
                voice=v,
                rate=r,
                volume=vol,
            )

            audio_buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])

            audio_bytes = audio_buffer.getvalue()
            logger.info(
                "TTS synthesized: voice=%s, rate=%s, text=%d chars, audio=%d bytes",
                v, r, len(text), len(audio_bytes),
            )
            return audio_bytes

        except Exception as e:
            logger.error("TTS synthesis error: %s", str(e))
            raise

    async def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        volume: Optional[str] = None,
    ) -> str:
        """Synthesize text to an MP3 file."""
        try:
            v = voice or settings.TTS_VOICE
            r = rate or settings.TTS_RATE
            vol = volume or settings.TTS_VOLUME

            communicate = edge_tts.Communicate(
                text=text,
                voice=v,
                rate=r,
                volume=vol,
            )
            await communicate.save(output_path)
            logger.info("TTS saved to: %s", output_path)
            return output_path

        except Exception as e:
            logger.error("TTS file synthesis error: %s", str(e))
            raise

    async def get_voices(self, language: Optional[str] = None) -> list[dict]:
        """Get available voices, optionally filtered by language."""
        voices = await self._get_voices()
        if language:
            lang_prefix = language.lower()
            voices = [v for v in voices if v.get("Locale", "").lower().startswith(lang_prefix)]
        return [
            {
                "name": v.get("ShortName", ""),
                "display_name": v.get("FriendlyName", ""),
                "locale": v.get("Locale", ""),
                "gender": v.get("Gender", ""),
            }
            for v in voices
        ]

    async def ping(self) -> bool:
        """Check if the TTS service is available."""
        try:
            voices = await self._get_voices()
            return len(voices) > 0
        except Exception:
            return False


tts_service = TextToSpeechService()
