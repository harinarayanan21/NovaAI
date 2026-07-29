import time
import uuid
import json
import logging
import contextvars

logger = logging.getLogger("novaai.request")

_request_ctx: contextvars.ContextVar = contextvars.ContextVar("request_ctx", default=None)


class RequestContext:
    @classmethod
    def get(cls) -> dict:
        ctx = _request_ctx.get()
        if ctx is None:
            return {
                "request_id": "",
                "user_id": "",
                "conversation_id": 0,
                "agent_route": [],
                "memory_hits": 0,
                "rag_hits": 0,
                "tool_calls": [],
            }
        return ctx

    @classmethod
    def set(cls, data: dict):
        _request_ctx.set(data)


class RequestLoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request_id = str(uuid.uuid4())[:12]
        start = time.perf_counter()
        ctx = {
            "request_id": request_id,
            "user_id": "",
            "conversation_id": 0,
            "agent_route": [],
            "memory_hits": 0,
            "rag_hits": 0,
            "tool_calls": [],
        }
        token = _request_ctx.set(ctx)

        status_code = 200

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                latency_header = f"{round((time.perf_counter() - start) * 1000, 2)}ms".encode()
                headers.append((b"x-response-time", latency_header))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            log_data = {
                "request_id": request_id,
                "method": scope.get("method", ""),
                "path": scope.get("path", ""),
                "status": status_code,
                "latency_ms": latency_ms,
                "user_id": ctx.get("user_id", ""),
                "agent_route": ctx.get("agent_route", []),
                "memory_hits": ctx.get("memory_hits", 0),
                "rag_hits": ctx.get("rag_hits", 0),
                "tool_calls": ctx.get("tool_calls", []),
            }
            logger.info(json.dumps(log_data))
            _request_ctx.reset(token)
