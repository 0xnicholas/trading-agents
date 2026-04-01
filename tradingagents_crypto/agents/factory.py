"""
Agent factory for creating agent instances.
"""
from __future__ import annotations

from typing import Any

from tradingagents_crypto.agents.registry import AgentRegistry
from tradingagents_crypto.agents.base import AgentConfig


class AgentFactory:
    """Factory for creating agent instances."""

    @staticmethod
    def create_analyst(
        analyst_type: str,
        llm: Any,
        config: AgentConfig | None = None,
    ) -> Any:
        """Create an analyst agent.

        Args:
            analyst_type: Type of analyst (e.g., "btc", "eth", "sol")
            llm: LLM instance to use
            config: Optional agent configuration

        Returns:
            An agent instance

        Raises:
            ValueError: If analyst_type is not registered
        """
        from tradingagents_crypto.agents.base import BaseAgent

        agent_cls = AgentRegistry.get_analyst(analyst_type)
        if not agent_cls:
            available = AgentRegistry.list_analysts()
            raise ValueError(
                f"Unknown analyst type: {analyst_type}. "
                f"Available: {available}"
            )

        if config is None:
            config = AgentConfig(name=analyst_type)

        return agent_cls(config=config, llm=llm)

    @staticmethod
    def create_trader(
        trader_type: str,
        llm: Any,
        config: AgentConfig | None = None,
    ) -> Any:
        """Create a trader agent.

        Args:
            trader_type: Type of trader (e.g., "crypto")
            llm: LLM instance to use
            config: Optional agent configuration

        Returns:
            A trader instance

        Raises:
            ValueError: If trader_type is not registered
        """
        from tradingagents_crypto.agents.base import BaseAgent

        agent_cls = AgentRegistry.get_trader(trader_type)
        if not agent_cls:
            available = AgentRegistry.list_traders()
            raise ValueError(
                f"Unknown trader type: {trader_type}. "
                f"Available: {available}"
            )

        if config is None:
            config = AgentConfig(name=trader_type)

        return agent_cls(config=config, llm=llm)
