import sys
import os
import time
import logging
from datetime import timezone, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
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
from backend.analytics.analytics_router import router as analytics_router
from backend.mcp.router import router as mcp_router
from backend.vision.image_router import router as vision_router
from backend.utils.logger import logger

from backend.models.user import User
from backend.models.conversation import Conversation
from backend.models.message import Message
from backend.models.document import Document
from backend.models.analytics import ChatMetric, ToolMetric, PerformanceMetric, AgentTrace, ErrorLog

_APP_START_TIME = time.time()

_app_version = settings.APP_VERSION


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured.")

    if settings.MEMORY_ENABLED:
        try:
            from backend.memory.redis_service import redis_service
            from backend.memory.chroma_service import chroma_service

            await redis_service.ping()
            logger.info("Redis service: %s", "fakeredis (fallback)" if redis_service.is_fallback else "connected")

            await chroma_service.ping()
            logger.info("ChromaDB service: connected")
        except Exception as e:
            logger.warning("Memory services partial init: %s", str(e))

    mcp_initialized = False
    if settings.MCP_SERVERS:
        try:
            from backend.mcp.manager import mcp_manager
            await mcp_manager.initialize()
            if settings.MCP_AUTO_CONNECT:
                results = await mcp_manager.connect_all()
                connected = sum(1 for r in results if r.get("success"))
                logger.info("MCP auto-connect: %d/%d servers connected", connected, len(results))
            mcp_initialized = True
        except Exception as e:
            logger.warning("MCP initialization failed: %s", e)

    yield

    if mcp_initialized:
        try:
            from backend.mcp.manager import mcp_manager
            await mcp_manager.disconnect_all()
        except Exception:
            pass
    await engine.dispose()
    logger.info("Database connections closed.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="NovaAI - Multi-Agent AI Assistant",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

app.add_middleware(GZipMiddleware, minimum_size=500, compresslevel=6)

if not settings.DEBUG:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.middleware("http")
async def request_size_middleware(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        max_bytes = settings.MAX_REQUEST_SIZE_MB * 1024 * 1024
        if int(content_length) > max_bytes:
            return Response(
                content='{"detail":"Request too large"}',
                status_code=413,
                media_type="application/json",
            )
    return await call_next(request)


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    import uuid
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Response-Time"] = f"{elapsed_ms}ms"
    return response


app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(conversations_router, prefix="/api")
app.include_router(memory_router, prefix="/api")
app.include_router(voice_router, prefix="/api")
app.include_router(rag_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(mcp_router, prefix="/api")
app.include_router(vision_router, prefix="/api")

from backend.security import RateLimitMiddleware
app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.RATE_LIMIT_REQUESTS,
    window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
)


@app.get("/health")
async def health_check():
    import asyncio

    checks = {}
    start_time = time.perf_counter()

    async def _check_db():
        from sqlalchemy import text
        from backend.database.session import async_session
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok"}

    async def _check_redis():
        from backend.memory.redis_service import redis_service
        await redis_service.ping()
        return {"status": "ok", "fallback": redis_service.is_fallback}

    async def _check_chroma():
        from backend.memory.chroma_service import chroma_service
        await chroma_service.ping()
        return {"status": "ok"}

    async def _check_langgraph():
        from backend.graph.graph_builder import graph_manager
        graph_manager.get_graph()
        return {"status": "ok", "nodes": 9}

    async def _check_voice():
        return {"status": "ok", "enabled": settings.VOICE_ENABLED}

    async def _check_rag():
        return {"status": "ok", "collection": settings.RAG_COLLECTION}

    async def _check_tools():
        from backend.tools.tool_manager import tool_manager
        tools = tool_manager.list_tools()
        return {"status": "ok", "tool_count": len(tools)}

    async def _check_analytics():
        from backend.analytics.metrics import metrics as m
        return {"status": "ok", "total_requests": m.get_counter("total_requests")}

    async def _check_vision():
        from backend.vision.image_knowledge import image_knowledge
        ok = await image_knowledge.ping()
        return {"status": "ok" if ok else "error", "image_kb": ok}

    async def _check_mcp():
        from backend.mcp.manager import mcp_manager
        health = await mcp_manager.health()
        summary = {}
        try:
            from backend.mcp.registry import registry
            summary = registry.get_summary()
        except Exception:
            pass
        return {
            "status": health.get("status", "ok") if mcp_manager._initialized else "not_initialized",
            **summary,
        }

    check_list = [
        ("database", _check_db, 5),
        ("redis", _check_redis, 3),
        ("chromadb", _check_chroma, 3),
        ("langgraph", _check_langgraph, 5),
        ("voice", _check_voice, 1),
        ("rag", _check_rag, 1),
        ("tool_manager", _check_tools, 3),
        ("analytics", _check_analytics, 1),
        ("vision", _check_vision, 3),
        ("mcp", _check_mcp, 3),
    ]

    for name, fn, timeout in check_list:
        try:
            checks[name] = await asyncio.wait_for(fn(), timeout=timeout)
        except asyncio.TimeoutError:
            checks[name] = {"status": "timeout"}
        except Exception as e:
            checks[name] = {"status": "error", "detail": str(e)[:100]}

    checks["groq"] = (
        {"status": "configured", "model": settings.GROQ_MODEL}
        if settings.GROQ_API_KEY
        else {"status": "not_configured"}
    )

    all_ok = all(
        c.get("status") in ("ok", "configured", "not_initialized")
        for c in checks.values()
    )

    uptime_seconds = round(time.time() - _APP_START_TIME, 2)

    return {
        "status": "healthy" if all_ok else "degraded",
        "version": _app_version,
        "uptime_seconds": uptime_seconds,
        "checks": checks,
    }


@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "version": _app_version, "status": "running"}


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting %s v%s", settings.APP_NAME, _app_version)
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug",
        access_log=settings.DEBUG,
    )
