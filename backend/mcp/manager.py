import asyncio
import json
import logging

from backend.config.settings import settings
from backend.mcp.client import MCPServerClient
from backend.mcp.registry import registry

logger = logging.getLogger(__name__)


class MCPManager:
    """Orchestrates connections to multiple MCP servers."""

    def __init__(self):
        self._clients: dict[str, MCPServerClient] = {}
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        servers = settings.MCP_SERVERS
        if not servers:
            logger.info("No MCP servers configured")
            self._initialized = True
            return

        for cfg in servers:
            name = cfg.get("name", "").strip()
            command = cfg.get("command", "").strip()
            args = cfg.get("args", [])
            if not name or not command:
                logger.warning("Skipping invalid MCP server config: %s", cfg)
                continue
            client = MCPServerClient(name=name, command=command, args=args)
            self._clients[name] = client
            registry.register_server(name, {
                "command": command,
                "args": args,
                "configured": True,
            })
            registry.set_status(name, "disconnected")

        self._initialized = True
        logger.info("MCP Manager initialized with %d server(s)", len(self._clients))

    async def connect(self, name: str) -> dict:
        client = self._clients.get(name)
        if not client:
            return {"success": False, "error": f"Unknown server: {name}"}
        try:
            await client.connect()
            registry.set_status(name, "connected")
            registry.update_tools(name, client.tools)
            return {"success": True, "name": name, "tools": len(client.tools)}
        except Exception as e:
            registry.set_status(name, "error")
            logger.error("Failed to connect MCP server %s: %s", name, e)
            return {"success": False, "name": name, "error": str(e)[:200]}

    async def disconnect(self, name: str) -> dict:
        client = self._clients.get(name)
        if not client:
            return {"success": False, "error": f"Unknown server: {name}"}
        try:
            await client.disconnect()
            registry.set_status(name, "disconnected")
            registry.update_tools(name, [])
            return {"success": True, "name": name}
        except Exception as e:
            logger.error("Failed to disconnect MCP server %s: %s", name, e)
            return {"success": False, "name": name, "error": str(e)[:200]}

    async def reconnect(self, name: str) -> dict:
        await self.disconnect(name)
        return await self.connect(name)

    async def connect_all(self) -> list[dict]:
        results = []
        for name in list(self._clients.keys()):
            result = await self.connect(name)
            results.append(result)
        return results

    async def disconnect_all(self) -> list[dict]:
        results = []
        for name in list(self._clients.keys()):
            result = await self.disconnect(name)
            results.append(result)
        return results

    async def refresh(self) -> list[dict]:
        results = []
        for name, client in self._clients.items():
            if client.connected:
                try:
                    tools = await client.list_tools()
                    registry.update_tools(name, tools)
                    results.append({"name": name, "tools": len(tools), "status": "refreshed"})
                except Exception as e:
                    registry.set_status(name, "error")
                    results.append({"name": name, "error": str(e)[:200], "status": "error"})
            else:
                results.append({"name": name, "status": "disconnected"})
        return results

    async def health(self) -> dict:
        server_details = {}
        all_ok = True
        for name, client in self._clients.items():
            h = await client.health()
            server_details[name] = h
            if h.get("status") != "ok":
                all_ok = False
        return {
            "status": "ok" if all_ok else "degraded",
            "connected": sum(1 for c in self._clients.values() if c.connected),
            "total": len(self._clients),
            "servers": server_details,
        }

    def get_client(self, name: str) -> MCPServerClient | None:
        return self._clients.get(name)

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict | None = None) -> dict:
        client = self._clients.get(server_name)
        if not client:
            return {"success": False, "error": f"Unknown server: {server_name}"}
        if not client.connected:
            return {"success": False, "error": f"Server {server_name} is not connected"}
        try:
            result = await client.call_tool(tool_name, arguments)
            return {"success": True, **result}
        except Exception as e:
            logger.error("MCP tool call failed: %s/%s: %s", server_name, tool_name, e)
            return {"success": False, "error": str(e)[:200]}

    async def list_all_tools(self) -> list[dict]:
        tools = []
        for name, client in self._clients.items():
            if client.connected:
                for t in client.tools:
                    tools.append({**t, "server": name})
        return tools


mcp_manager = MCPManager()
