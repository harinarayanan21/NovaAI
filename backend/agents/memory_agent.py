import logging
from backend.graph.state import AgentState

logger = logging.getLogger(__name__)


async def memory_agent_node(state: AgentState) -> dict:
    """Memory agent that retrieves relevant long-term memories.

    Integrates with the existing memory_manager to search ChromaDB
    and inject relevant memories into the graph state.
    """
    try:
        from backend.memory.memory_manager import memory_manager

        user_id = state.get("user_id", "")
        conversation_id = state.get("conversation_id", 0)
        user_message = state.get("user_message", "")
        history = state.get("conversation_history", [])

        context = await memory_manager.build_context(
            user_id=user_id,
            conversation_id=conversation_id,
            current_message=user_message,
            recent_messages=history,
        )

        retrieved = context.get("relevant_memories", [])

        user_memories = context.get("user_memories", [])

        system_prompt = await memory_manager.build_system_prompt(context)

        logger.info(
            "Memory agent: retrieved %d relevant memories, %d total for user %s",
            len(retrieved),
            len(user_memories),
            user_id,
        )

        return {
            "retrieved_memories": retrieved,
            "system_prompt": system_prompt,
            "metadata": {
                **state.get("metadata", {}),
                "memory_agent_relevant_count": len(retrieved),
                "memory_agent_total_count": len(user_memories),
                "memory_agent_completed": True,
            },
        }

    except Exception as e:
        logger.error("Memory agent error: %s", str(e))
        return {
            "retrieved_memories": [],
            "errors": state.get("errors", []) + [f"memory_agent: {str(e)[:200]}"],
        }
