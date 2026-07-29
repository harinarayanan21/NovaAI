import logging
from backend.graph.state import AgentState

logger = logging.getLogger(__name__)


async def chat_agent_node(state: AgentState) -> dict:
    """Chat agent responsible for natural language generation.

    This agent uses all available context (memories, documents, tool results,
    planning steps) to generate the final human-readable response.
    """
    try:
        from backend.services.groq_service import groq_service

        system_prompt = state.get("system_prompt", "")

        context_parts = []
        if state.get("retrieved_memories"):
            context_parts.append("## User Memories")
            for mem in state["retrieved_memories"][:5]:
                context_parts.append(f"- {mem.get('content', '')}")

        if state.get("retrieved_documents"):
            context_parts.append("## Relevant Document Content")
            for doc in state["retrieved_documents"][:3]:
                context_parts.append(
                    f"[Source: {doc.get('filename', 'unknown')}]\n{doc.get('content', '')}"
                )

        if state.get("tool_results"):
            context_parts.append("## Tool Results")
            for tr in state["tool_results"]:
                context_parts.append(
                    f"- {tr.get('tool_name', 'unknown')}: {tr.get('result', '')[:300]}"
                )

        if state.get("planning_steps"):
            context_parts.append("## Execution Plan")
            for i, step in enumerate(state["planning_steps"], 1):
                context_parts.append(f"{i}. {step}")

        if context_parts:
            system_prompt += "\n\n" + "\n\n".join(context_parts)

        history = state.get("conversation_history", [])

        response, tools_used = await groq_service.chat(
            state["user_message"],
            history=history,
            system_prompt=system_prompt,
        )

        final_response = response if response else "I'm sorry, I couldn't generate a response."

        return {
            "final_response": final_response,
            "metadata": {
                **state.get("metadata", {}),
                "chat_agent_tools_used": tools_used,
                "chat_agent_completed": True,
            },
        }

    except Exception as e:
        logger.error("Chat agent error: %s", str(e))
        error_msg = str(e)
        if "429" in error_msg or "rate limit" in error_msg.lower():
            friendly = "I'm currently experiencing high demand. Please try again in a few minutes."
        else:
            friendly = "I encountered an error while processing your request."
        return {
            "final_response": friendly,
            "errors": state.get("errors", []) + [f"chat_agent: {str(e)[:200]}"],
        }
