"""
Solana data layer - unified entry point.

Aggregates all SOL-related data:
- Spot price (CoinCap)
- DEX liquidity (GeckoTerminal - placeholder)
- Meme coins (GeckoTerminal - placeholder)
"""
import logging
from datetime import datetime, timezone
from typing import Any, Callable, TypeVar

from tradingagents_crypto.dataflows.hyperliquid.cache import CacheManager

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _safe_get(
    func: Callable[[], T],
    field_name: str,
    default: Any,
) -> T:
    """
    Safely call a function and return default on failure.

    Args:
        func: Function to call
        field_name: Name for logging
        default: Default value on failure

    Returns:
        Result of func() or default
    """
    try:
        return func()
    except Exception as e:
        logger.warning(f"Failed to get {field_name}: {e}")
        return default


def get_sol_data(
    symbol: str = "SOL",
    use_cache: bool = True,
) -> dict:
    """
    Get comprehensive SOL data from all sources.

    Args:
        symbol: Currently only "SOL" supported
        use_cache: Whether to use cache (default True)

    Returns:
        Dict with:
        - symbol: str
        - spot_price: dict from CoinCap
        - dex: dict with liquidity data
        - meme: list of meme coin data
        - timestamp: datetime
    """
    cache = CacheManager() if use_cache else None

    # Import here to avoid circular imports
    from . import price as sol_price
    from . import dex as sol_dex
    from . import meme as sol_meme

    result = {
        "symbol": symbol,
        "timestamp": datetime.now(timezone.utc),
    }

    # Get spot price
    result["spot_price"] = _safe_get(
        lambda: sol_price.get_sol_price(cache=cache),
        "SOL spot price",
        {"price_usd": 0.0, "confidence": 0.0},
    )

    # Get DEX liquidity
    result["dex"] = _safe_get(
        lambda: sol_dex.get_dex_liquidity(symbol, cache=cache),
        "DEX liquidity",
        {"token": symbol, "total_tvl": 0.0, "confidence": 0.0},
    )

    # Get meme coins (if SOL)
    if symbol == "SOL":
        result["meme"] = _safe_get(
            lambda: sol_meme.get_meme_coins(limit=10, cache=cache),
            "Meme coins",
            [],
        )
    else:
        result["meme"] = []

    return result
