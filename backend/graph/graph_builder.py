import logging
import time
from typing import Literal
from langgraph.graph import StateGraph, END
from backend.graph.state import AgentState

logger = logging.getLogger(__name__)


def _route_after_supervisor(state: AgentState) -> list[str]:
    routed = state.get("routed_agents", ["chat_agent"])

    node_map = {
        "memory_agent": "memory_agent",
        "rag_agent": "rag_agent",
        "tool_agent": "tool_agent",
        "planning_agent": "planning_agent",
        "voice_agent": "voice_agent",
        "mcp_agent": "mcp_agent",
        "vision_agent": "vision_agent",
        "chat_agent": "chat_agent",
    }

    next_nodes = []
    for agent in routed:
        if agent in node_map and agent not in next_nodes:
            next_nodes.append(node_map[agent])

    if not next_nodes:
        next_nodes = ["chat_agent"]

    if "chat_agent" not in next_nodes:
        next_nodes.append("chat_agent")

    logger.info("Routing to nodes: %s", next_nodes)
    return next_nodes


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    from backend.agents.supervisor import supervisor_node
    from backend.agents.chat_agent import chat_agent_node
    from backend.agents.memory_agent import memory_agent_node
    from backend.agents.rag_agent import rag_agent_node
    from backend.agents.tool_agent import tool_agent_node
    from backend.agents.planning_agent import planning_agent_node
    from backend.agents.voice_agent import voice_agent_node
    from backend.agents.mcp_agent import mcp_agent_node
    from backend.agents.vision_agent import vision_agent_node

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("memory_agent", memory_agent_node)
    graph.add_node("rag_agent", rag_agent_node)
    graph.add_node("tool_agent", tool_agent_node)
    graph.add_node("planning_agent", planning_agent_node)
    graph.add_node("voice_agent", voice_agent_node)
    graph.add_node("mcp_agent", mcp_agent_node)
    graph.add_node("vision_agent", vision_agent_node)
    graph.add_node("chat_agent", chat_agent_node)

    graph.set_entry_point("supervisor")

    graph.add_conditional_edges(
        "supervisor",
        _route_after_supervisor,
        {
            "memory_agent": "memory_agent",
            "rag_agent": "rag_agent",
            "tool_agent": "tool_agent",
            "planning_agent": "planning_agent",
            "voice_agent": "voice_agent",
            "mcp_agent": "mcp_agent",
            "vision_agent": "vision_agent",
            "chat_agent": "chat_agent",
        },
    )

    graph.add_edge("memory_agent", "chat_agent")
    graph.add_edge("rag_agent", "chat_agent")
    graph.add_edge("tool_agent", "chat_agent")
    graph.add_edge("planning_agent", "chat_agent")
    graph.add_edge("voice_agent", "chat_agent")
    graph.add_edge("mcp_agent", "chat_agent")
    graph.add_edge("vision_agent", "chat_agent")
    graph.add_edge("chat_agent", END)

    compiled = graph.compile()
    logger.info("LangGraph compiled successfully with 9 nodes")
    return compiled


class GraphManager:
    def __init__(self):
        self._graph = None

    def get_graph(self):
        if self._graph is None:
            self._graph = build_graph()
        return self._graph

    async def invoke(self, state: AgentState) -> AgentState:
        graph = self.get_graph()
        start = time.perf_counter()
        trace_steps = []

        original_nodes = {}
        trace_data = {"steps": trace_steps, "start_time": start}

        def _make_traced(name, original_fn):
            async def traced(state_inner):
                step_start = time.perf_counter()
                try:
                    result = await original_fn(state_inner)
                    step_ms = round((time.perf_counter() - step_start) * 1000, 2)
                    trace_steps.append({
                        "agent": name,
                        "latency_ms": step_ms,
                        "status": "completed",
                        "agents_routed": result.get("routed_agents") if "routed_agents" in result else None,
                    })
                    return result
                except Exception as e:
                    step_ms = round((time.perf_counter() - step_start) * 1000, 2)
                    trace_steps.append({
                        "agent": name,
                        "latency_ms": step_ms,
                        "status": "error",
                        "error": str(e)[:200],
                    })
                    raise
            return traced

        from backend.agents.supervisor import supervisor_node
        from backend.agents.chat_agent import chat_agent_node
        from backend.agents.memory_agent import memory_agent_node
        from backend.agents.rag_agent import rag_agent_node
        from backend.agents.tool_agent import tool_agent_node
        from backend.agents.planning_agent import planning_agent_node
        from backend.agents.voice_agent import voice_agent_node
        from backend.agents.mcp_agent import mcp_agent_node
        from backend.agents.vision_agent import vision_agent_node

        node_fns = {
            "supervisor": supervisor_node,
            "chat_agent": chat_agent_node,
            "memory_agent": memory_agent_node,
            "rag_agent": rag_agent_node,
            "tool_agent": tool_agent_node,
            "planning_agent": planning_agent_node,
            "voice_agent": voice_agent_node,
            "mcp_agent": mcp_agent_node,
            "vision_agent": vision_agent_node,
        }

        compiled_graph = self._graph

        from langgraph.graph import StateGraph as SG
        traced_graph = SG(AgentState)
        for name, fn in node_fns.items():
            traced_graph.add_node(name, _make_traced(name, fn))

        traced_graph.set_entry_point("supervisor")
        traced_graph.add_conditional_edges(
            "supervisor",
            _route_after_supervisor,
            {
                "memory_agent": "memory_agent",
                "rag_agent": "rag_agent",
                "tool_agent": "tool_agent",
                "planning_agent": "planning_agent",
                "voice_agent": "voice_agent",
                "mcp_agent": "mcp_agent",
                "vision_agent": "vision_agent",
                "chat_agent": "chat_agent",
            },
        )
        traced_graph.add_edge("memory_agent", "chat_agent")
        traced_graph.add_edge("rag_agent", "chat_agent")
        traced_graph.add_edge("tool_agent", "chat_agent")
        traced_graph.add_edge("planning_agent", "chat_agent")
        traced_graph.add_edge("voice_agent", "chat_agent")
        traced_graph.add_edge("mcp_agent", "chat_agent")
        traced_graph.add_edge("vision_agent", "chat_agent")
        traced_graph.add_edge("chat_agent", END)

        traced_compiled = traced_graph.compile()

        result = await traced_compiled.ainvoke(state)

        total_ms = round((time.perf_counter() - start) * 1000, 2)
        result["metadata"] = {
            **result.get("metadata", {}),
            "agent_trace": trace_steps,
            "total_latency_ms": total_ms,
        }

        logger.info(
            "Graph execution completed in %dms, trace: %s",
            total_ms,
            [s["agent"] for s in trace_steps],
        )

        return result

    def get_graph_visualization(self) -> str:
        return (
            "Graph: START -> supervisor -> [memory_agent | rag_agent | tool_agent | "
            "planning_agent | voice_agent | mcp_agent | vision_agent | chat_agent] -> chat_agent -> END"
        )


graph_manager = GraphManager()
