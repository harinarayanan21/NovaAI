import logging
from typing import Optional
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class GroqService:
    """Service for interacting with Groq LLM via LangChain."""

    def __init__(self):
        self._llm = None

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
    ) -> str:
        """Send a message to Groq with optional history and return the response."""
        try:
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
        except Exception as e:
            logger.error("Groq API error: %s", str(e))
            raise


groq_service = GroqService()
