import json
import logging
from typing import Optional
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Redis service for short-term memory (session cache, recent messages)."""

    def __init__(self):
        self._client = None
        self._is_fake = False

    def _get_client(self):
        """Lazy-initialize Redis client with fakeredis fallback."""
        if self._client is not None:
            return self._client

        if settings.REDIS_USE_FAKE:
            try:
                import fakeredis
                self._client = fakeredis.FakeRedis(decode_responses=True)
                self._is_fake = True
                logger.info("Using fakeredis (in-memory) for short-term memory")
                return self._client
            except Exception as e:
                logger.warning("fakeredis failed: %s", str(e))

        try:
            import redis
            self._client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=3,
            )
            self._client.ping()
            self._is_fake = False
            logger.info("Connected to Redis at %s", settings.REDIS_URL)
            return self._client
        except Exception as e:
            logger.warning("Redis not available, falling back to fakeredis: %s", str(e))
            try:
                import fakeredis
                self._client = fakeredis.FakeRedis(decode_responses=True)
                self._is_fake = True
                logger.info("Using fakeredis (in-memory) fallback")
                return self._client
            except Exception as e2:
                logger.error("Failed to initialize any Redis client: %s", str(e2))
                return None

    @property
    def is_available(self) -> bool:
        return self._get_client() is not None

    @property
    def is_fallback(self) -> bool:
        return self._is_fake

    def _session_key(self, user_id: str, conversation_id: int) -> str:
        return f"session:{user_id}:{conversation_id}"

    def _recent_key(self, user_id: str) -> str:
        return f"recent:{user_id}"

    def _user_prefix(self, user_id: str) -> str:
        return f"user:{user_id}:*"

    async def add_message(self, user_id: str, conversation_id: int, role: str, content: str) -> bool:
        """Add a message to the session's recent messages list."""
        client = self._get_client()
        if not client:
            return False
        try:
            key = self._session_key(user_id, conversation_id)
            msg = json.dumps({"role": role, "content": content})
            client.rpush(key, msg)
            client.ltrim(key, -settings.REDIS_MAX_RECENT_MESSAGES, -1)
            client.expire(key, settings.REDIS_SESSION_TTL)
            return True
        except Exception as e:
            logger.error("Redis add_message error: %s", str(e))
            return False

    async def get_recent_messages(self, user_id: str, conversation_id: int, limit: int = 20) -> list[dict]:
        """Get recent messages from session cache."""
        client = self._get_client()
        if not client:
            return []
        try:
            key = self._session_key(user_id, conversation_id)
            messages = client.lrange(key, -limit, -1)
            return [json.loads(m) for m in messages]
        except Exception as e:
            logger.error("Redis get_recent_messages error: %s", str(e))
            return []

    async def set_session(self, user_id: str, conversation_id: int, data: dict) -> bool:
        """Store session metadata."""
        client = self._get_client()
        if not client:
            return False
        try:
            key = f"meta:{user_id}:{conversation_id}"
            client.setex(key, settings.REDIS_SESSION_TTL, json.dumps(data))
            return True
        except Exception as e:
            logger.error("Redis set_session error: %s", str(e))
            return False

    async def get_session(self, user_id: str, conversation_id: int) -> Optional[dict]:
        """Get session metadata."""
        client = self._get_client()
        if not client:
            return None
        try:
            key = f"meta:{user_id}:{conversation_id}"
            data = client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error("Redis get_session error: %s", str(e))
            return None

    async def set_conversation_summary(self, user_id: str, conversation_id: int, summary: str) -> bool:
        """Cache a conversation summary."""
        client = self._get_client()
        if not client:
            return False
        try:
            key = f"summary:{user_id}:{conversation_id}"
            client.setex(key, settings.REDIS_CACHE_TTL, summary)
            return True
        except Exception as e:
            logger.error("Redis set_conversation_summary error: %s", str(e))
            return False

    async def get_conversation_summary(self, user_id: str, conversation_id: int) -> Optional[str]:
        """Get cached conversation summary."""
        client = self._get_client()
        if not client:
            return None
        try:
            key = f"summary:{user_id}:{conversation_id}"
            return client.get(key)
        except Exception as e:
            logger.error("Redis get_conversation_summary error: %s", str(e))
            return None

    async def clear_user_data(self, user_id: str) -> bool:
        """Clear all cached data for a user."""
        client = self._get_client()
        if not client:
            return False
        try:
            pattern = f"*:{user_id}:*"
            keys = client.keys(pattern)
            if keys:
                client.delete(*keys)
            return True
        except Exception as e:
            logger.error("Redis clear_user_data error: %s", str(e))
            return False

    async def ping(self) -> bool:
        """Check if Redis is reachable."""
        client = self._get_client()
        if not client:
            return False
        try:
            return client.ping()
        except Exception:
            return False


redis_service = RedisService()
