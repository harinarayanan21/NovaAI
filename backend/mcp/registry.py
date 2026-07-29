import threading
from datetime import datetime, timezone


class MCPRegistry:
    """Thread-safe registry that tracks MCP server connections, tools, and status."""

    def __init__(self):
        self._lock = threading.RLock()
        self._servers: dict[str, dict] = {}
        self._tools: dict[str, list[dict]] = {}
        self._status: dict[str, str] = {}

    def register_server(self, name: str, info: dict):
        with self._lock:
            self._servers[name] = {
                **info,
                "registered_at": datetime.now(timezone.utc).isoformat(),
            }
            if name not in self._status:
                self._status[name] = "disconnected"

    def unregister_server(self, name: str):
        with self._lock:
            self._servers.pop(name, None)
            self._tools.pop(name, None)
            self._status.pop(name, None)

    def update_tools(self, server_name: str, tools: list[dict]):
        with self._lock:
            self._tools[server_name] = tools

    def set_status(self, server_name: str, status: str):
        with self._lock:
            self._status[server_name] = status

    def get_servers(self) -> dict[str, dict]:
        with self._lock:
            return dict(self._servers)

    def get_tools(self) -> dict[str, list[dict]]:
        with self._lock:
            return dict(self._tools)

    def get_all_tools_flat(self) -> list[dict]:
        with self._lock:
            result = []
            for server, tools in self._tools.items():
                for t in tools:
                    result.append({**t, "server": server})
            return result

    def get_status(self) -> dict[str, str]:
        with self._lock:
            return dict(self._status)

    def get_server_names(self) -> list[str]:
        with self._lock:
            return list(self._servers.keys())

    def get_summary(self) -> dict:
        with self._lock:
            connected = sum(
                1 for s in self._status.values() if s == "connected"
            )
            total = len(self._servers)
            tool_count = sum(len(t) for t in self._tools.values())
            return {
                "total_servers": total,
                "connected_servers": connected,
                "disconnected_servers": total - connected,
                "total_tools": tool_count,
            }


registry = MCPRegistry()
