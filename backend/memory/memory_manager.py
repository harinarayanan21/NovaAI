import re
import logging
from typing import Optional
from backend.config.settings import settings
from backend.memory.redis_service import redis_service
from backend.memory.chroma_service import chroma_service
from backend.memory.embedding_service import embedding_service

logger = logging.getLogger(__name__)

# Patterns that indicate important user information
MEMORY_PATTERNS = [
    (r"(?:my|i'?m|i am)\s+name(?:'s| is|s)?\s+(.+)", "name"),
    (r"(?:i|my)\s+(?:like|prefer|love|enjoy|want)\s+(.+)", "preference"),
    (r"(?:i|my)\s+(?:live|reside|am from|am in)\s+(.+)", "location"),
    (r"(?:i|my)\s+(?:work|am working on|am building|am developing)\s+(.+)", "project"),
    (r"(?:i|my)\s+(?:graduat|finish|complete)\s+(?:in\s+)?(.+)", "goal"),
    (r"(?:i|my)\s+(?:know|know how to|am good at|am skilled in)\s+(.+)", "skill"),
    (r"(?:i|my)\s+(?:need|want|would like)\s+(.+)", "preference"),
    (r"(?:i|my)\s+(?:am|'m)\s+(?:a|an|the)?\s*(.+?)(?:\.|$)", "fact"),
    (r"(?:please|always|never)\s+(.+)", "preference"),
]

CATEGORY_LABELS = {
    "name": "Names",
    "preference": "Preferences",
    "location": "Location",
    "project": "Projects",
    "goal": "Goals",
    "skill": "Skills",
    "fact": "Facts",
    "general": "General",
}


class MemoryManager:
    """Orchestrates the memory pipeline: Redis + ChromaDB + Groq context."""

    def should_store_as_memory(self, message: str) -> tuple[bool, str, str]:
        """Analyze if a message contains storable information. Returns (should_store, content, category)."""
        msg_lower = message.lower().strip()
        for pattern, category in MEMORY_PATTERNS:
            match = re.search(pattern, msg_lower)
            if match:
                return True, message.strip(), category
        if len(message) > 15 and any(
            kw in msg_lower
            for kw in ["my name", "i like", "i live", "i work", "i prefer",
                        "i am", "i'm", "i need", "i want", "i know",
                        "i study", "i use", "my favorite", "my project"]
        ):
            return True, message.strip(), "general"
        return False, "", "general"

    async def build_context(
        self,
        user_id: str,
        conversation_id: int,
        current_message: str,
        recent_messages: list[dict],
    ) -> dict:
        """Build enriched context for the LLM using Redis + ChromaDB."""
        context = {
            "recent_messages": recent_messages,
            "relevant_memories": [],
            "user_memories": [],
        }
        if not settings.MEMORY_ENABLED:
            return context

        # 1. Get recent messages from Redis cache
        cached_messages = await redis_service.get_recent_messages(
            user_id, conversation_id
        )
        if cached_messages and not recent_messages:
            context["recent_messages"] = cached_messages

        # 2. Search ChromaDB for relevant memories
        relevant = await chroma_service.search_memories(
            user_id=user_id,
            query=current_message,
            n_results=settings.MEMORY_MAX_RESULTS,
        )
        context["relevant_memories"] = relevant

        # 3. Get all user memories for system prompt
        all_memories = await chroma_service.get_user_memories(user_id=user_id, limit=50)
        context["user_memories"] = all_memories

        return context

    async def process_message(
        self,
        user_id: str,
        conversation_id: int,
        role: str,
        content: str,
    ) -> None:
        """Process a message: store in Redis and optionally extract long-term memory."""
        # Always store in Redis for session cache
        await redis_service.add_message(user_id, conversation_id, role, content)

        # Only analyze user messages for long-term memory
        if role != "user" or not settings.MEMORY_ENABLED:
            return

        # Check if message contains important information
        should_store, memory_content, category = self.should_store_as_memory(content)
        if should_store:
            memory_id = await chroma_service.add_memory(
                user_id=user_id,
                content=memory_content,
                category=category,
                conversation_id=conversation_id,
            )
            if memory_id:
                logger.info(
                    "Auto-stored memory for user %s: [%s] %s",
                    user_id, category, memory_content[:50],
                )

    async def build_system_prompt(self, context: dict) -> str:
        """Build an enhanced system prompt with memory context."""
        base_prompt = (
            "You are a helpful, friendly, and knowledgeable AI assistant. "
            "Provide clear, concise, and accurate responses."
        )

        if not context.get("relevant_memories") and not context.get("user_memories"):
            return base_prompt

        memory_section = "\n\n## User Context & Memories\n"
        memory_section += "Use the following information about the user to personalize your responses:\n\n"

        if context.get("user_memories"):
            memory_section += "**Stored Facts:**\n"
            for mem in context["user_memories"][:15]:
                cat = CATEGORY_LABELS.get(
                    mem["metadata"].get("category", "general"), "General"
                )
                memory_section += f"- [{cat}] {mem['content']}\n"

        if context.get("relevant_memories"):
            memory_section += "\n**Relevant to Current Query:**\n"
            for mem in context["relevant_memories"][:5]:
                memory_section += f"- {mem['content']} (similarity: {mem['similarity']})\n"

        memory_section += (
            "\nUse these memories to provide personalized, context-aware responses. "
            "Do not explicitly mention that you have stored memories unless asked."
        )

        return base_prompt + memory_section

    async def get_stats(self, user_id: str) -> dict:
        """Get memory statistics for a user."""
        stats = await chroma_service.get_memory_stats(user_id)
        stats["redis_available"] = redis_service.is_available
        stats["redis_fallback"] = redis_service.is_fallback
        stats["chromadb_available"] = await chroma_service.ping()
        stats["embedding_model"] = settings.EMBEDDING_MODEL
        stats["categories"] = {
            CATEGORY_LABELS.get(k, k): v
            for k, v in stats.get("categories", {}).items()
        }
        return stats

    async def search(self, user_id: str, query: str, category: Optional[str] = None) -> list[dict]:
        """Search memories for a user."""
        return await chroma_service.search_memories(
            user_id=user_id,
            query=query,
            n_results=settings.MEMORY_MAX_RESULTS,
            category=category,
        )

    async def get_memories(
        self, user_id: str, category: Optional[str] = None
    ) -> list[dict]:
        """Get all memories for a user."""
        return await chroma_service.get_user_memories(user_id=user_id, category=category)

    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """Delete a specific memory."""
        return await chroma_service.delete_memory(memory_id, user_id)

    async def clear_user_memories(self, user_id: str) -> bool:
        """Clear all memories for a user."""
        await redis_service.clear_user_data(user_id)
        return await chroma_service.delete_user_memories(user_id)


memory_manager = MemoryManager()
