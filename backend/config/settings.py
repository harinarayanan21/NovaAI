import json
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "NovaAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Groq Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE", "0.7"))
    GROQ_MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS", "1024"))

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./ai_assistant.db",
    )

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # CORS
    CORS_ORIGINS: list = json.loads(os.getenv("CORS_ORIGINS", '["http://localhost:5173","http://localhost:3000"]'))

    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_USE_FAKE: bool = os.getenv("REDIS_USE_FAKE", "true").lower() == "true"
    REDIS_SESSION_TTL: int = int(os.getenv("REDIS_SESSION_TTL", "3600"))
    REDIS_CACHE_TTL: int = int(os.getenv("REDIS_CACHE_TTL", "86400"))
    REDIS_MAX_RECENT_MESSAGES: int = int(os.getenv("REDIS_MAX_RECENT_MESSAGES", "20"))

    # ChromaDB Configuration
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION", "memories")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

    # Memory Configuration
    MEMORY_ENABLED: bool = os.getenv("MEMORY_ENABLED", "true").lower() == "true"
    MEMORY_SIMILARITY_THRESHOLD: float = float(os.getenv("MEMORY_SIMILARITY_THRESHOLD", "0.6"))
    MEMORY_MAX_RESULTS: int = int(os.getenv("MEMORY_MAX_RESULTS", "10"))
    MEMORY_IMPORTANCE_THRESHOLD: float = float(os.getenv("MEMORY_IMPORTANCE_THRESHOLD", "0.7"))

    # Voice Configuration - STT
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "tiny")
    WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "cpu")
    WHISPER_COMPUTE_TYPE: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    WHISPER_LANGUAGE: str = os.getenv("WHISPER_LANGUAGE", "en")
    WHISPER_beam_size: int = int(os.getenv("WHISPER_BEAM_SIZE", "5"))

    # Voice Configuration - TTS
    TTS_VOICE: str = os.getenv("TTS_VOICE", "en-US-GuyNeural")
    TTS_RATE: str = os.getenv("TTS_RATE", "+0%")
    TTS_VOLUME: str = os.getenv("TTS_VOLUME", "+0%")
    TTS_OUTPUT_FORMAT: str = os.getenv("TTS_OUTPUT_FORMAT", "audio-24khz-96kbitrate-mono-mp3")

    # Voice Configuration - General
    VOICE_ENABLED: bool = os.getenv("VOICE_ENABLED", "true").lower() == "true"
    MAX_AUDIO_SIZE_MB: int = int(os.getenv("MAX_AUDIO_SIZE_MB", "25"))
    MAX_AUDIO_DURATION_SEC: int = int(os.getenv("MAX_AUDIO_DURATION_SEC", "120"))

    # RAG Configuration
    RAG_CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "800"))
    RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "200"))
    RAG_MAX_FILE_SIZE_MB: int = int(os.getenv("RAG_MAX_FILE_SIZE_MB", "20"))
    RAG_DEFAULT_RESULTS: int = int(os.getenv("RAG_DEFAULT_RESULTS", "5"))
    RAG_COLLECTION: str = os.getenv("RAG_COLLECTION", "documents")

    # Vision Configuration
    VISION_ENABLED: bool = os.getenv("VISION_ENABLED", "true").lower() == "true"
    VISION_MAX_FILE_SIZE_MB: int = int(os.getenv("VISION_MAX_FILE_SIZE_MB", "20"))
    VISION_UPLOAD_DIR: str = os.getenv("VISION_UPLOAD_DIR", "uploads/vision")

    # MCP Configuration
    MCP_SERVERS: list = json.loads(os.getenv("MCP_SERVERS", "[]"))
    MCP_AUTO_CONNECT: bool = os.getenv("MCP_AUTO_CONNECT", "true").lower() == "true"

    # Security & Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    ALLOWED_HOSTS: list = json.loads(os.getenv("ALLOWED_HOSTS", '["*"]'))
    MAX_REQUEST_SIZE_MB: int = int(os.getenv("MAX_REQUEST_SIZE_MB", "50"))

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
