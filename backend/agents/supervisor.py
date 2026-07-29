import json
import logging
from backend.graph.state import AgentState

logger = logging.getLogger(__name__)

SUPERVISOR_PROMPT = """You are a supervisor agent that routes user messages to the appropriate specialist agents.

Available agents:
- chat_agent: For general conversation, greetings, and natural language tasks.
- memory_agent: When the user references past conversations, personal info, or asks "do you remember...".
- rag_agent: When the user asks about uploaded documents, PDFs, or knowledge base content.
- tool_agent: When the user needs math calculations, date/time, random generation, weather, or web search.
- planning_agent: For complex multi-step tasks that require breaking down into ordered steps.
- voice_agent: When voice input is detected (voice_data is present in state).
- mcp_agent: When the user asks about external services accessed via MCP (Model Context Protocol) — e.g. GitHub repos, Google Drive, Gmail, databases, or any third-party API tool connected through MCP servers. Add mcp_agent alongside tool_agent when the request involves external APIs.
- vision_agent: When the user asks about image content, uploads an image, needs OCR/text extraction from images, wants chart analysis, UI screenshot analysis, or visual question answering. Also triggered when voice_data includes an image.

Analyze the user message and decide which agents to invoke. You may invoke multiple agents.

Respond with a JSON object containing:
- "agents": list of agent names to invoke (e.g. ["memory_agent", "chat_agent"])
- "reasoning": brief explanation of why these agents were chosen

Examples:
- "Hello!" → {"agents": ["chat_agent"], "reasoning": "Simple greeting"}
- "What is 2+2?" → {"agents": ["tool_agent", "chat_agent"], "reasoning": "Math question needs calculator"}
- "What did I say about my project?" → {"agents": ["memory_agent", "chat_agent"], "reasoning": "References past conversations"}
- "Summarize my uploaded PDF about AI" → {"agents": ["rag_agent", "chat_agent"], "reasoning": "Questions about uploaded documents"}
- "List my GitHub repositories" → {"agents": ["mcp_agent", "chat_agent"], "reasoning": "Uses MCP to access GitHub"}
- "Search my Google Drive for the report" → {"agents": ["mcp_agent", "chat_agent"], "reasoning": "Uses MCP to search Google Drive"}
- "Describe this image" → {"agents": ["vision_agent", "chat_agent"], "reasoning": "Image description needed"}
- "What text is in this screenshot?" → {"agents": ["vision_agent", "chat_agent"], "reasoning": "OCR on image"}
- "Analyze this chart" → {"agents": ["vision_agent", "chat_agent"], "reasoning": "Chart analysis needed"}
- "Calculate the weather in London and tell me a joke" → {"agents": ["tool_agent", "chat_agent"], "reasoning": "Multiple tasks: weather + joke"}
- Complex request → {"agents": ["planning_agent", "tool_agent", "chat_agent"], "reasoning": "Multi-step task"}
"""


async def supervisor_node(state: AgentState) -> dict:
    """Supervisor node that routes requests to appropriate agents.

    Inspects the user message and decides which agents need to run.
    Writes the routing decision into state.metadata.
    """
    try:
        from backend.services.groq_service import groq_service

        user_message = state["user_message"]
        has_voice = state.get("voice_data") is not None

        if has_voice:
            return {
                "routed_agents": ["voice_agent", "memory_agent", "chat_agent"],
                "metadata": {
                    **state.get("metadata", {}),
                    "supervisor_reasoning": "Voice input detected, routing to voice processing",
                    "supervisor_agents": ["voice_agent", "memory_agent", "chat_agent"],
                },
            }

        response = await groq_service._plain_chat(
            user_message,
            history=[{"role": "system", "content": SUPERVISOR_PROMPT}],
            system_prompt=SUPERVISOR_PROMPT,
        )

        try:
            parsed = json.loads(response) if isinstance(response, str) else response
            agents = parsed.get("agents", ["chat_agent"])
            reasoning = parsed.get("reasoning", "Default routing")
        except (json.JSONDecodeError, AttributeError):
            agents = ["chat_agent"]
            reasoning = "Failed to parse supervisor response, defaulting to chat"

        if "chat_agent" not in agents:
            agents.append("chat_agent")

        agents = list(dict.fromkeys(agents))

        logger.info(
            "Supervisor routed to %s: %s", agents, reasoning
        )

        return {
            "routed_agents": agents,
            "metadata": {
                **state.get("metadata", {}),
                "supervisor_reasoning": reasoning,
                "supervisor_agents": agents,
            },
        }

    except Exception as e:
        logger.error("Supervisor error: %s", str(e))
        return {
            "routed_agents": ["chat_agent"],
            "metadata": {
                **state.get("metadata", {}),
                "supervisor_reasoning": f"Error in supervisor, defaulting to chat: {str(e)}",
                "supervisor_agents": ["chat_agent"],
            },
            "errors": state.get("errors", []) + [f"supervisor: {str(e)[:200]}"],
        }
