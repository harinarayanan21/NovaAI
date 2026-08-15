import json
import logging
from backend.graph.state import AgentState

logger = logging.getLogger(__name__)


async def tool_agent_node(state: AgentState) -> dict:
    """Tool agent that executes tools via the existing tool_manager.

    Delegates to the existing Step 7 tool infrastructure.
    Does not rewrite any tool implementations.
    """
    try:
        from backend.services.groq_service import groq_service
        from backend.tools.tool_manager import tool_manager

        user_message = state["user_message"]
        system_prompt = state.get("system_prompt", "")

        # Tools are bound natively via bind_tools. Never inject textual tool
        # descriptions into the prompt — doing so makes llama models emit
        # malformed <function=...> text instead of native tool_calls.
        tools = tool_manager.get_langchain_tools()
        llm_with_tools = groq_service._get_llm_with_tools(tools)

        from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
        messages = [SystemMessage(content=system_prompt)]

        history = state.get("conversation_history", [])
        for msg in history[-6:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                from langchain_core.messages import AIMessage
                messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=user_message))

        response = await groq_service._invoke_llm(llm_with_tools, messages)
        tool_results = []

        if response.tool_calls:
            logger.info("tool_calls: %s", [tc["name"] for tc in response.tool_calls])
            messages.append(response)
            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                logger.info("executed_tool: %s(%s)", tool_name, tool_args)

                result = await tool_manager.execute_tool(tool_name, tool_args)
                messages.append(ToolMessage(content=result, tool_call_id=tc["id"]))

                logger.info("tool_result (%s): %s", tool_name, str(result)[:200])

                tool_results.append({
                    "tool_name": tool_name,
                    "arguments": tool_args,
                    "result": str(result)[:500],
                })

            response = await groq_service._invoke_llm(llm_with_tools, messages)

        return {
            "tool_results": tool_results,
            "metadata": {
                **state.get("metadata", {}),
                "tool_agent_tools_executed": [tr["tool_name"] for tr in tool_results],
                "tool_agent_completed": True,
            },
        }

    except Exception as e:
        logger.error("Tool agent error: %s", str(e))
        return {
            "tool_results": state.get("tool_results", []),
            "errors": state.get("errors", []) + [f"tool_agent: {str(e)[:200]}"],
        }
