import json
import logging
import re
from typing import Optional
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from backend.config.settings import settings

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 5

# Matches raw text tool invocations like "<web_search({...})" or
# "<function=web_search{...}" that llama models occasionally emit in
# response.content instead of a structured tool_call.
RAW_TOOL_CALL_RE = re.compile(r"<\s*[a-zA-Z_][a-zA-Z0-9_]*\s*(?:\(|\{|=)")


class GroqService:
    """Service for interacting with Groq LLM via LangChain, with optional tool calling."""

    def __init__(self):
        self._llm = None
        self._llm_with_tools = None
        self._tools = None

    def _get_llm(self) -> ChatGroq:
        """Lazy-initialize the Groq LLM client."""
        if self._llm is None:
            if not settings.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY is not set in environment variables.")
            self._llm = ChatGroq(
                groq_api_key=settings.GROQ_API_KEY,
                model_name=settings.GROQ_MODEL,
                temperature=settings.GROQ_TEMPERATURE,
                max_tokens=settings.GROQ_MAX_TOKENS,
            )
            logger.info("Groq LLM initialized with model: %s", settings.GROQ_MODEL)
        return self._llm

    def _get_llm_with_tools(self, tools: list):
        """Get LLM bound with tools (cached per tool set)."""
        if self._llm_with_tools is None or self._tools != tools:
            llm = self._get_llm()
            self._llm_with_tools = llm.bind_tools(tools)
            self._tools = tools
            logger.info("LLM bound with %d tools", len(tools))
        return self._llm_with_tools

    async def _invoke_llm(self, llm, messages: list, attempts: int = 3):
        """Invoke an LLM, retrying when Groq rejects a malformed tool call.

        llama-3.3-70b-versatile intermittently emits malformed <function=...>
        text instead of a valid structured tool call. Groq rejects it with a
        400 'tool_use_failed' error carrying the raw invocation text. Retrying
        the same request lets the model produce a valid call on the next try.
        """
        last_err = None
        for attempt in range(attempts):
            try:
                return await llm.ainvoke(messages)
            except Exception as e:
                last_err = e
                err = str(e)
                if "tool_use_failed" not in err and "failed_generation" not in err:
                    raise
                logger.warning(
                    "Groq rejected malformed tool call (attempt %d/%d)",
                    attempt + 1,
                    attempts,
                )
        raise last_err

    def _build_messages(
        self,
        system_prompt: str,
        history: Optional[list[dict]] = None,
        user_message: str = "",
    ) -> list:
        """Build LangChain message list from system prompt, history + new message."""
        messages = [SystemMessage(content=system_prompt)]
        if history:
            for msg in history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=user_message))
        return messages

    async def chat(
        self,
        message: str,
        history: Optional[list[dict]] = None,
        system_prompt: Optional[str] = None,
    ) -> tuple[str, list[dict]]:
        """Send a message to Groq with optional history and return the response.

        Returns:
            Tuple of (response_text, tool_calls_info) where tool_calls_info is a
            list of dicts with keys: tool_name, arguments, result_summary.
        """
        try:
            from backend.tools.tool_manager import tool_manager

            llm = self._get_llm()
            prompt = system_prompt or (
                "You are a helpful, friendly, and knowledgeable AI assistant. "
                "Provide clear, concise, and accurate responses."
            )
            messages = self._build_messages(
                system_prompt=prompt, history=history, user_message=message
            )

            tools = tool_manager.get_langchain_tools()
            llm_with_tools = self._get_llm_with_tools(tools)
            tools_used: list[dict] = []

            response = await self._invoke_llm(llm_with_tools, messages)

            if not response.tool_calls:
                content = response.content or ""
                if RAW_TOOL_CALL_RE.search(content):
                    logger.warning(
                        "LLM returned raw tool invocation text in content; "
                        "falling back to plain chat"
                    )
                    return await self._plain_chat(message, history, system_prompt), []
                return content, tools_used

            logger.info("LLM requested %d tool calls", len(response.tool_calls))

            for round_num in range(MAX_TOOL_ROUNDS):
                messages.append(response)

                for tc in response.tool_calls:
                    tool_name = tc["name"]
                    tool_args = tc["args"]
                    logger.info("Tool call [%d]: %s(%s)", round_num, tool_name, tool_args)

                    result = await tool_manager.execute_tool(tool_name, tool_args)
                    messages.append(
                        ToolMessage(content=result, tool_call_id=tc["id"])
                    )

                    result_summary = str(result)[:200] if result else ""
                    tools_used.append({
                        "tool_name": tool_name,
                        "arguments": tool_args,
                        "result_summary": result_summary,
                    })

                response = await self._invoke_llm(llm_with_tools, messages)

                if not response.tool_calls:
                    break

                logger.info("LLM requested more tool calls (round %d)", round_num + 1)

            final = response.content or ""
            if RAW_TOOL_CALL_RE.search(final):
                logger.warning(
                    "Final response was raw tool invocation text; "
                    "falling back to plain chat"
                )
                return await self._plain_chat(message, history, system_prompt), tools_used
            if not final and tools_used:
                final = "I've processed your request using available tools."

            return final, tools_used

        except ImportError:
            logger.warning("Tools module not available, falling back to plain chat")
            result = await self._plain_chat(message, history, system_prompt)
            return result, []
        except Exception as e:
            logger.error("Groq API error: %s", str(e))
            raise

    async def _plain_chat(
        self,
        message: str,
        history: Optional[list[dict]] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Plain chat without tool calling (fallback)."""
        llm = self._get_llm()
        prompt = system_prompt or (
            "You are a helpful, friendly, and knowledgeable AI assistant. "
            "Provide clear, concise, and accurate responses."
        )
        messages = self._build_messages(
            system_prompt=prompt, history=history, user_message=message
        )
        response = await llm.ainvoke(messages)
        return response.content


groq_service = GroqService()
