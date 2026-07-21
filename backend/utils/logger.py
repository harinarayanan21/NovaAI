import logging
import sys
from backend.config.settings import settings


def setup_logger(name: str = "ai_assistant") -> logging.Logger:
    """Configure and return a application logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] %(levelname)s in %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    return logger


logger = setup_logger()
