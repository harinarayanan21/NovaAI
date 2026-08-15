import logging
from backend.graph.state import AgentState
from backend.mcp.manager import mcp_manager
from backend.mcp.registry import registry
from backend.analytics.metrics import metrics

logger = logging.getLogger(__name__)


async def mcp_agent_node(state: AgentState) -> dict:
    """MCP agent that executes tool calls on connected MCP servers.
    Triggered by the supervisor when MCP-related requests are detected.
    """
    try:
        user_message = state.get("user_message", "")
        mcp_data = state.get("mcp_data", {})

        tools = registry.get_all_tools_flat()
        if not tools:
            return {
                "mcp_data": {
                    **mcp_data,
                    "note": "No MCP tools available. Connect to an MCP server first.",
                    "tools_available": 0,
                },
                "metadata": {
                    **state.get("metadata", {}),
                    "mcp_agent_completed": True,
                    "mcp_tools_available": 0,
                },
            }

        description = "\n".join(
            f"- {t['name']} ({t['server']}): {t.get('description', '')[:100]}"
            for t in tools
        )

        from backend.services.groq_service import groq_service

        system_prompt = (
            "You have access to external MCP (Model Context Protocol) servers with these tools:\n"
            f"{description}\n\n"
            "Determine which tool to use based on the user's request. "
            "Respond with a JSON object with:\n"
            '- "tool": the tool name to call\n'
            '- "server": the server name\n'
            '- "arguments": dict of arguments for the tool\n'
            '- "reasoning": brief explanation\n\n'
            "If no tool is needed, respond with {\"tool\": null}."
        )

        response = await groq_service._plain_chat(
            user_message,
            history=[{"role": "system", "content": system_prompt}],
            system_prompt=system_prompt,
        )

        import json as json_mod

        try:
            parsed = json_mod.loads(response) if isinstance(response, str) else response
        except (json_mod.JSONDecodeError, TypeError):
            parsed = {"tool": None}

        tool_name = parsed.get("tool")
        if tool_name:
            server_name = parsed.get("server", "")
            arguments = parsed.get("arguments", {})
            reasoning = parsed.get("reasoning", "")

            if not server_name:
                for t in tools:
                    if t["name"] == tool_name:
                        server_name = t["server"]
                        break

            logger.info(
                "MCP agent calling %s/%s: %s",
                server_name, tool_name, reasoning,
            )

            import time
            t0 = time.perf_counter()
            result = await mcp_manager.call_tool(server_name, tool_name, arguments)
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

            metrics.increment(f"mcp_tool_{tool_name}")
            metrics.record_latency(f"mcp_{server_name}", elapsed_ms)

            return {
                "mcp_data": {
                    **mcp_data,
                    "last_tool_call": {
                        "server": server_name,
                        "tool": tool_name,
                        "arguments": arguments,
                        "result": result.get("content", str(result)),
                        "latency_ms": elapsed_ms,
                    },
                    "tools_available": len(tools),
                },
                "tool_results": [{
                    "tool_name": f"mcp:{server_name}/{tool_name}",
                    "arguments": arguments,
                    "result": result.get("content", str(result))[:500],
                }],
                "metadata": {
                    **state.get("metadata", {}),
                    "mcp_agent_completed": True,
                    "mcp_tools_available": len(tools),
                    "mcp_tool_executed": tool_name,
                    "mcp_server": server_name,
                },
            }

        return {
            "mcp_data": {
                **mcp_data,
                "tools_available": len(tools),
                "note": "No MCP tool needed for this request",
            },
            "metadata": {
                **state.get("metadata", {}),
                "mcp_agent_completed": True,
                "mcp_tools_available": len(tools),
            },
        }

    except Exception as e:
        logger.error("MCP agent error: %s", e)
        return {
            "errors": state.get("errors", []) + [f"mcp_agent: {str(e)[:200]}"],
            "metadata": {
                **state.get("metadata", {}),
                "mcp_agent_error": str(e)[:200],
            },
        }
