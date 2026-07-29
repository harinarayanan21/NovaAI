import logging

logger = logging.getLogger(__name__)


class MCPServerClient:
    """Manages a single MCP server connection using the stdio transport."""

    def __init__(self, name: str, command: str, args: list[str] | None = None):
        self.name = name
        self.command = command
        self.args = args or []
        self._session = None
        self._read_stream = None
        self._write_stream = None
        self._stdio_cm = None
        self._tools: list[dict] = []
        self._capabilities: dict = {}
        self._server_info: dict = {}
        self.connected = False
        self.error: str | None = None

    async def connect(self):
        from mcp.client.stdio import stdio_client, StdioServerParameters
        from mcp.client.session import ClientSession

        params = StdioServerParameters(command=self.command, args=self.args)
        self._stdio_cm = stdio_client(params)
        self._read_stream, self._write_stream = await self._stdio_cm.__aenter__()

        self._session = ClientSession(self._read_stream, self._write_stream)
        await self._session.__aenter__()

        init_result = await self._session.initialize()
        caps = init_result.capabilities
        self._capabilities = {}
        if caps:
            for field in ("experimental", "logging", "prompts", "resources", "tools", "completions"):
                val = getattr(caps, field, None)
                if val is not None:
                    self._capabilities[field] = True
            if caps.extensions:
                self._capabilities["extensions"] = list(caps.extensions.keys())

        self._server_info = {
            "name": init_result.server_info.name if init_result.server_info else "",
            "version": init_result.server_info.version if init_result.server_info else "",
        }

        await self._refresh_tools()
        self.connected = True
        self.error = None
        logger.info("MCP connected: %s (%d tools)", self.name, len(self._tools))

    async def _refresh_tools(self):
        from mcp import types

        result = await self._session.list_tools()
        self._tools = []
        for t in result.tools:
            schema = {}
            if hasattr(t, "input_schema") and t.input_schema:
                schema = t.input_schema
            elif hasattr(t, "inputSchema") and t.inputSchema:
                schema = t.inputSchema
            self._tools.append({
                "name": t.name,
                "description": t.description or "",
                "input_schema": schema,
                "title": getattr(t, "title", None) or "",
            })

    async def disconnect(self):
        if self._session:
            try:
                await self._session.__aexit__(None, None, None)
            except Exception as e:
                logger.warning("MCP session close error (%s): %s", self.name, e)
            self._session = None
        if self._stdio_cm:
            try:
                await self._stdio_cm.__aexit__(None, None, None)
            except Exception as e:
                logger.warning("MCP stdio close error (%s): %s", self.name, e)
            self._stdio_cm = None
        self.connected = False
        self._tools = []
        logger.info("MCP disconnected: %s", self.name)

    async def health(self) -> dict:
        if not self.connected or not self._session:
            return {"status": "disconnected"}
        try:
            await self._session.send_ping()
            return {
                "status": "ok",
                "tools": len(self._tools),
            }
        except Exception as e:
            self.error = str(e)[:200]
            return {"status": "error", "detail": self.error}

    async def list_tools(self) -> list[dict]:
        if not self.connected or not self._session:
            return []
        try:
            await self._refresh_tools()
            return self._tools
        except Exception as e:
            logger.warning("Failed to list tools for %s: %s", self.name, e)
            return self._tools

    async def call_tool(self, tool_name: str, arguments: dict | None = None) -> dict:
        from mcp import types

        result = await self._session.call_tool(tool_name, arguments or {})
        content_text = ""
        is_error = False
        if isinstance(result, types.CallToolResult):
            is_error = getattr(result, "is_error", False) or False
            for item in getattr(result, "content", []) or []:
                if isinstance(item, types.TextContent):
                    content_text += item.text + "\n"
                elif hasattr(item, "text"):
                    content_text += str(item.text) + "\n"
                else:
                    content_text += str(item) + "\n"
        else:
            content_text = str(result)

        return {
            "content": content_text.strip(),
            "is_error": is_error,
            "tool_name": tool_name,
        }

    @property
    def tools(self) -> list[dict]:
        return self._tools

    @property
    def capabilities(self) -> dict:
        return self._capabilities
