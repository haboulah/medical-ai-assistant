# Base agent class for all agents.
"""Abstract base class for all agents in the multi-agent system."""

from __future__ import annotations

from abc import ABC, abstractmethod

from langchain_core.messages import BaseMessage
from langchain_groq import ChatGroq

from app.core import settings
from app.monitoring.service import Timer


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, name: str):
        self.name = name
        self.llm = self._create_llm() if settings.is_groq_configured else None

    def _create_llm(self) -> ChatGroq:
        """Create the Groq LLM instance."""
        return ChatGroq(
            model=settings.GROQ_MODEL_NAME,
            temperature=settings.GROQ_TEMPERATURE,
            max_tokens=settings.GROQ_MAX_TOKENS,
            api_key=settings.GROQ_API_KEY,
        )

    @abstractmethod
    def process(self, state: dict) -> dict:
        """Process the input and return the result."""
        ...

    def execute(self, state: dict) -> dict:
        """Execute the agent with timing."""
        timer = Timer(self.name)
        with timer:
            result = self.process(state)

        result["agent_name"] = self.name
        result["execution_time_ms"] = timer.elapsed_ms
        return result

    def get_token_count(self, messages: list[BaseMessage]) -> int:
        """Estimate token count from messages."""
        total = 0
        for msg in messages:
            if hasattr(msg, "content") and isinstance(msg.content, str):
                total += len(msg.content) // 4  # Approximate: ~4 chars per token
        return total
