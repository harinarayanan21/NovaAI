import logging
import operator
from typing import TypedDict, Optional, Annotated

logger = logging.getLogger(__name__)


def _merge_dicts(current: dict, incoming: dict) -> dict:
    """Merge dicts from concurrent nodes so no keys are overwritten."""
    merged = dict(current or {})
    merged.update(incoming or {})
    return merged


def _merge_unique(current: list, incoming: list) -> list:
    """Append lists while de-duplicating (used for errors)."""
    result = list(current or [])
    for item in incoming or []:
        if item not in result:
            result.append(item)
    return result


class AgentState(TypedDict):
    """Shared state that flows through the entire LangGraph workflow.

    Every agent reads from and writes to this state. The graph ensures
    consistency across all nodes.

    Keys written by multiple concurrent nodes use Annotated reducers so
    LangGraph merges their updates instead of raising
    INVALID_CONCURRENT_GRAPH_UPDATE.
    """

    user_message: str
    user_id: str
    conversation_id: int
    conversation_history: list[dict]
    retrieved_memories: list[dict]
    retrieved_documents: list[dict]
    tool_results: Annotated[list[dict], operator.add]
    planning_steps: list[str]
    final_response: str
    metadata: Annotated[dict, _merge_dicts]
    system_prompt: str
    routed_agents: list[str]
    errors: Annotated[list[str], _merge_unique]
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
