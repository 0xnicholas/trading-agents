"""Analysts package."""

from tradingagents_crypto.agents.analysts.hyperliquid_perp_analyst import (
    create_hyperliquid_analyst,
    analyze_hyperliquid_perp,
    HYPERLIQUID_ANALYST_PROMPT,
)
from tradingagents_crypto.agents.analysts.ethereum_onchain_analyst import (
    analyze_ethereum_onchain,
    EthereumOnChainReport,
    EthereumOnChainSignals,
    ETH_ANALYST_PROMPT,
)
from tradingagents_crypto.agents.analysts.solana_dex_analyst import (
    analyze_solana_dex,
    SolanaDexReport,
    SolanaDexSignals,
    SOLANA_ANALYST_PROMPT,
)
from tradingagents_crypto.agents.analysts.cross_chain_macro_analyst import (
    analyze_cross_chain_macro,
    CrossChainMacroReport,
    CrossChainSignals,
    MACRO_ANALYST_PROMPT,
)

__all__ = [
    "create_hyperliquid_analyst",
    "analyze_hyperliquid_perp",
    "HYPERLIQUID_ANALYST_PROMPT",
    "analyze_ethereum_onchain",
    "EthereumOnChainReport",
    "EthereumOnChainSignals",
    "ETH_ANALYST_PROMPT",
    "analyze_solana_dex",
    "SolanaDexReport",
    "SolanaDexSignals",
    "SOLANA_ANALYST_PROMPT",
    "analyze_cross_chain_macro",
    "CrossChainMacroReport",
    "CrossChainSignals",
    "MACRO_ANALYST_PROMPT",
]
