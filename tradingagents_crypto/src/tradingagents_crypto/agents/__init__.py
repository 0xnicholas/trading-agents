"""
Crypto trading agents.

Includes analysts, traders, and tools.
"""
from tradingagents_crypto.agents.base import (
    AgentConfig,
    CryptoAgentBase,
    AnalystReport,
    TradingDecision,
)
from tradingagents_crypto.agents.analysts.hyperliquid_perp_analyst import (
    create_hyperliquid_analyst,
    analyze_hyperliquid_perp,
    create_analyst_node,
    HYPERLIQUID_ANALYST_PROMPT,
)
from tradingagents_crypto.agents.traders.crypto_trader import (
    CryptoTrader,
    create_trader_node,
    TRADER_PROMPT,
)
from tradingagents_crypto.agents.registry import AgentRegistry
from tradingagents_crypto.agents.factory import AgentFactory

__all__ = [
    # Base
    "AgentConfig",
    "CryptoAgentBase",
    "AnalystReport",
    "TradingDecision",
    # Analysts
    "create_hyperliquid_analyst",
    "analyze_hyperliquid_perp",
    "create_analyst_node",
    "HYPERLIQUID_ANALYST_PROMPT",
    # Traders
    "CryptoTrader",
    "create_trader_node",
    "TRADER_PROMPT",
    # Factory
    "AgentRegistry",
    "AgentFactory",
]
