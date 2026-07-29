import logging
from typing import TypedDict, Optional

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """Shared state that flows through the entire LangGraph workflow.

    Every agent reads from and writes to this state. The graph ensures
    consistency across all nodes.
    """

    user_message: str
    user_id: str
    conversation_id: int
    conversation_history: list[dict]
    retrieved_memories: list[dict]
    retrieved_documents: list[dict]
    tool_results: list[dict]
    planning_steps: list[str]
    final_response: str
    metadata: dict
    system_prompt: str
    routed_agents: list[str]
    errors: list[str]
    voice_data: Optional[dict]
    mcp_data: dict
    vision_data: dict


def create_initial_state(
    user_message: str,
    user_id: str,
    conversation_id: int,
    conversation_history: list[dict] = None,
    voice_data: dict = None,
) -> AgentState:
    """Create the initial state for a new workflow execution."""
    return AgentState(
        user_message=user_message,
        user_id=str(user_id),
        conversation_id=conversation_id,
        conversation_history=conversation_history or [],
        retrieved_memories=[],
        retrieved_documents=[],
        tool_results=[],
        planning_steps=[],
        final_response="",
        metadata={},
        system_prompt=(
            "You are a helpful, friendly, and knowledgeable AI assistant. "
            "Provide clear, concise, and accurate responses."
        ),
        routed_agents=[],
        errors=[],
        voice_data=voice_data,
        mcp_data={},
        vision_data={},
    )
