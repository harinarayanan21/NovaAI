import json
import logging
from typing import Any
from langchain_core.tools import BaseTool
from backend.tools.calculator import calculator
from backend.tools.datetime_tool import datetime_tool
from backend.tools.random_tool import random_integer, random_password, generate_otp, generate_uuid
from backend.tools.weather import get_weather
from backend.tools.search import web_search

logger = logging.getLogger(__name__)

ALL_TOOLS: list[BaseTool] = [
    calculator,
    datetime_tool,
    random_integer,
    random_password,
    generate_otp,
    generate_uuid,
    get_weather,
    web_search,
]

TOOL_MAP: dict[str, BaseTool] = {t.name: t for t in ALL_TOOLS}


class ToolManager:
    """Central dispatcher for tool execution."""

    def __init__(self):
        self.tools = ALL_TOOLS
        self.tool_map = TOOL_MAP

    def get_langchain_tools(self) -> list[BaseTool]:
        """Return all tools in LangChain format for binding to the LLM."""
        return self.tools

    def get_tool_descriptions(self) -> str:
        """Return formatted tool descriptions for system prompt injection."""
        lines = []
        for tool in self.tools:
            args_desc = ""
            if tool.args:
                arg_parts = []
                for name, schema in tool.args.items():
                    desc = schema.get("description", "")
                    arg_parts.append(f"  - {name}: {desc}")
                args_desc = "\n".join(arg_parts)
            lines.append(f"- {tool.name}: {tool.description}\n{args_desc}")
        return "\n\n".join(lines)

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Execute a tool by name with the given arguments.

        Returns:
            JSON string result from the tool.
        """
        if tool_name not in self.tool_map:
            logger.warning("Unknown tool: %s", tool_name)
            return json.dumps({
                "success": False,
                "error": f"Unknown tool: {tool_name}. Available: {list(self.tool_map.keys())}",
            })

        tool = self.tool_map[tool_name]
        logger.info("Executing tool: %s with args: %s", tool_name, arguments)

        try:
            result = await tool.ainvoke(arguments)
            logger.info("Tool %s result: %s", tool_name, str(result)[:200])
            return result
        except Exception as e:
            logger.error("Tool execution error (%s): %s", tool_name, str(e))
            return json.dumps({"success": False, "error": str(e)})

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool exists."""
        return tool_name in self.tool_map

    def list_tools(self) -> list[dict]:
        """List all available tools with metadata."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.args,
            }
            for tool in self.tools
        ]


tool_manager = ToolManager()
