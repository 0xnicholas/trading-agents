"""
Solana DEX data.

Data sources:
- GeckoTerminal: DEX pools and liquidity
- Note: Jupiter is blocked, CoinCap as fallback
"""
import logging

logger = logging.getLogger(__name__)

DEFAULT_TTL = 300  # 5 minutes


def get_dex_liquidity(
    token: str = "SOL",
    cache=None,
) -> dict:
    """
    Get DEX liquidity for a Solana token.

    Note: GeckoTerminal API not tested due to VM network restrictions.
    This returns a placeholder - implement when API is accessible.

    Args:
        token: Token symbol (e.g., "SOL", "DOGE", "WIF")

    Returns:
        Dict with:
        - token: str
        - jupiter_tvl: float (0 until API accessible)
        - geckoterminal_tvl: float
        - total_tvl: float
        - confidence: float
    """
    # TODO: Implement GeckoTerminal API call when network is available
    return {
        "token": token,
        "jupiter_tvl": 0.0,  # Jupiter blocked
        "geckoterminal_tvl": 0.0,
        "total_tvl": 0.0,
        "confidence": 0.3,
        "note": "GeckoTerminal API not accessible from VM",
    }


def get_pool_info(pool_address: str) -> dict:
    """
    Get info for a specific DEX pool.

    Note: Placeholder - implement when API is accessible.
    """
    return {
        "pool_address": pool_address,
        "tvl": 0.0,
        "volume_24h": 0.0,
        "confidence": 0.3,
        "note": "Not implemented - API not accessible",
    }
