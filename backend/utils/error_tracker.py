import traceback
import logging

logger = logging.getLogger("novaai.errors")


def capture_exception(
    exc: Exception,
    request_id: str = "",
    endpoint: str = "",
    user_id: str = "",
) -> dict:
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    stack_trace = "".join(tb)

    error_data = {
        "error_type": type(exc).__name__,
        "error_message": str(exc)[:500],
        "stack_trace": stack_trace,
        "request_id": request_id,
        "endpoint": endpoint,
        "user_id": user_id,
    }

    logger.error(
        "Unhandled exception [%s] %s: %s\n%s",
        request_id or "no-req",
        endpoint or "unknown",
        str(exc)[:200],
        stack_trace,
    )

    return error_data
