"""
Base classes for crypto trading agents.

Provides common functionality for all agent types.
"""
from __future__ import annotations
import logging
from typing import Any, Callable, TypeVar, Annotated
from dataclasses import dataclass, field

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class AgentConfig:
    """Configuration for a trading agent."""
    model_name: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout_seconds: int = 60


class CryptoAgentBase:
    """
    Base class for all crypto trading agents.

    Provides common patterns for:
    - Tool binding
    - Prompt templating
    - State management
    - LLM invocation
    """

    def __init__(
        self,
        name: str,
        description: str,
        tools: list[Any],
        config: AgentConfig | None = None,
    ):
        self.name = name
        self.description = description
        self.tools = tools
        self.config = config or AgentConfig()

    def build_system_prompt(self, extra_context: str = "") -> str:
        """
        Build the system prompt for this agent.

        Override in subclasses for custom prompts.
        """
        return (
            f"You are {self.name}, a crypto trading analysis agent. "
            f"{self.description}. "
            f"{extra_context}"
        )

    def create_prompt(
        self,
        system_extra: str = "",
        message_key: str = "messages",
    ) -> ChatPromptTemplate:
        """
        Create a standard prompt template for this agent.

        Args:
            system_extra: Additional context to add to system prompt
            message_key: Key for messages placeholder in state

        Returns:
            ChatPromptTemplate configured for this agent
        """
        system_prompt = self.build_system_prompt(system_extra)

        return ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}"),
            MessagesPlaceholder(variable_name=message_key),
        ])

    def bind_tools(self, llm) -> Any:
        """Bind this agent's tools to an LLM."""
        return llm.bind_tools(self.tools)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, tools={len(self.tools)})"


@dataclass
class AnalystReport:
    """Standard output from an analyst agent."""
    summary: str
    direction: str  # "bullish" | "bearish" | "neutral"
    confidence: float  # 0.0 - 1.0
    signals: dict[str, Any]
    metrics: dict[str, Any]
    narrative: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "direction": self.direction,
            "confidence": self.confidence,
            "signals": self.signals,
            "metrics": self.metrics,
            "narrative": self.narrative,
        }


@dataclass
class TradingDecision:
    """Standard output from a trading decision."""
    action: str  # "long" | "short" | "close" | "hold"
    size_pct: float  # 0.0 - 1.0
    leverage: int  # 1 - 20
    reason: str
    risk_warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "size_pct": self.size_pct,
            "leverage": self.leverage,
            "reason": self.reason,
            "risk_warnings": self.risk_warnings,
        }
