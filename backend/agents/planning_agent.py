import json
import logging
from backend.graph.state import AgentState

logger = logging.getLogger(__name__)

PLANNING_PROMPT = """You are a planning agent. Given a complex user request, break it down into ordered steps.

Return a JSON object with:
- "steps": list of strings, each being a concrete actionable step
- "agents_needed": list of agent names needed (from: tool_agent, memory_agent, rag_agent, chat_agent)

Be concise. Each step should be a single actionable task. Aim for 2-5 steps.

Example:
User: "Calculate the factorial of 20, check the weather in Paris, and write a summary"
Response: {"steps": ["Calculate factorial of 20 using calculator", "Get weather in Paris using weather tool", "Write summary combining results"], "agents_needed": ["tool_agent", "chat_agent"]}
"""


async def planning_agent_node(state: AgentState) -> dict:
    """Planning agent for complex multi-step tasks.

    Breaks tasks into ordered steps, stores execution plan in state,
    and allows iterative execution.
    """
    try:
        from backend.services.groq_service import groq_service

        user_message = state["user_message"]

        response = await groq_service._plain_chat(
            user_message,
            history=[{"role": "system", "content": PLANNING_PROMPT}],
            system_prompt=PLANNING_PROMPT,
        )

        try:
            parsed = json.loads(response) if isinstance(response, str) else response
            steps = parsed.get("steps", [])
            agents_needed = parsed.get("agents_needed", ["chat_agent"])
        except (json.JSONDecodeError, AttributeError):
            steps = [f"Process the request: {user_message[:200]}"]
            agents_needed = ["tool_agent", "chat_agent"]

        logger.info("Planning agent: %d steps planned, agents: %s", len(steps), agents_needed)

        new_routed = list(state.get("routed_agents", []))
        for agent in agents_needed:
            if agent not in new_routed:
                new_routed.append(agent)
        if "chat_agent" not in new_routed:
            new_routed.append("chat_agent")

        return {
            "planning_steps": steps,
            "routed_agents": new_routed,
            "metadata": {
                **state.get("metadata", {}),
                "planning_agent_steps": steps,
                "planning_agent_agents_needed": agents_needed,
                "planning_agent_completed": True,
            },
        }

    except Exception as e:
        logger.error("Planning agent error: %s", str(e))
        return {
            "planning_steps": [f"Process: {state.get('user_message', '')[:200]}"],
            "errors": state.get("errors", []) + [f"planning_agent: {str(e)[:200]}"],
        }
