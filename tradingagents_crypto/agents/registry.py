"""
Agent registry for tracking available agent types.
"""
from __future__ import annotations

from typing import Type


class AgentRegistry:
    """Registry for agent types (analysts and traders)."""

    _analysts: dict[str, Type] = {}
    _traders: dict[str, Type] = {}

    @classmethod
    def register_analyst(cls, name: str):
        """Decorator to register an Analyst class.

        Usage:
            @AgentRegistry.register_analyst("btc")
            class BTCAnalyst(BaseAgent):
                ...
        """
        def decorator(agent_cls: Type) -> Type:
            cls._analysts[name] = agent_cls
            return agent_cls
        return decorator

    @classmethod
    def register_trader(cls, name: str):
        """Decorator to register a Trader class.

        Usage:
            @AgentRegistry.register_trader("crypto")
            class CryptoTrader(BaseAgent):
                ...
        """
        def decorator(agent_cls: Type) -> Type:
            cls._traders[name] = agent_cls
            return agent_cls
        return decorator

    @classmethod
    def get_analyst(cls, name: str) -> Type | None:
        """Get an analyst class by name."""
        return cls._analysts.get(name)

    @classmethod
    def get_trader(cls, name: str) -> Type | None:
        """Get a trader class by name."""
        return cls._traders.get(name)

    @classmethod
    def list_analysts(cls) -> list[str]:
        """List all registered analyst names."""
        return list(cls._analysts.keys())

    @classmethod
    def list_traders(cls) -> list[str]:
        """List all registered trader names."""
        return list(cls._traders.keys())

    @classmethod
    def clear(cls):
        """Clear all registrations (useful for testing)."""
        cls._analysts.clear()
        cls._traders.clear()
