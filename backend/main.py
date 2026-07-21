import sys
import os

# Ensure backend package is importable when running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config.settings import settings
from backend.database.base import Base
from backend.database.session import engine
from backend.api.chat import router as chat_router
from backend.api.auth import router as auth_router
from backend.api.users import router as users_router
from backend.api.conversations import router as conversations_router
from backend.memory.memory_router import router as memory_router
from backend.voice.voice_router import router as voice_router
from backend.rag.rag_router import router as rag_router
from backend.utils.logger import logger

# Import all models so Alembic / create_all can discover them
from backend.models.user import User  # noqa: F401
from backend.models.conversation import Conversation  # noqa: F401
from backend.models.message import Message  # noqa: F401
from backend.models.document import Document  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables and initialize memory services on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured.")

    # Initialize memory services
    if settings.MEMORY_ENABLED:
        try:
            from backend.memory.redis_service import redis_service
            from backend.memory.chroma_service import chroma_service
            from backend.memory.embedding_service import embedding_service

            await redis_service.ping()
            logger.info("Redis service: %s", "fakeredis (fallback)" if redis_service.is_fallback else "connected")

            await chroma_service.ping()
            logger.info("ChromaDB service: connected")

            # Pre-load embedding model
            _ = embedding_service.dimension
            logger.info("Embedding service: loaded")
        except Exception as e:
            logger.warning("Memory services initialization warning: %s", str(e))

    yield

    await engine.dispose()
    logger.info("Database connections closed.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Assistant API powered by Groq",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public routes
app.include_router(auth_router, prefix="/api")

# Protected routes
app.include_router(users_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(conversations_router, prefix="/api")
app.include_router(memory_router, prefix="/api")
app.include_router(voice_router, prefix="/api")
app.include_router(rag_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
