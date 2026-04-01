"""
Solana data layer - unified entry point.

Aggregates all SOL-related data:
- Spot price (CoinCap)
- DEX liquidity (GeckoTerminal - placeholder)
- Meme coins (GeckoTerminal - placeholder)
"""
import logging
from datetime import datetime, timezone

from tradingagents_crypto.dataflows.hyperliquid.cache import CacheManager

logger = logging.getLogger(__name__)


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
    try:
        result["spot_price"] = sol_price.get_sol_price(cache=cache)
    except Exception as e:
        logger.warning(f"Failed to get SOL spot price: {e}")
        result["spot_price"] = {"price_usd": 0.0, "confidence": 0.0}

    # Get DEX liquidity
    try:
        result["dex"] = sol_dex.get_dex_liquidity(symbol, cache=cache)
    except Exception as e:
        logger.warning(f"Failed to get DEX liquidity: {e}")
        result["dex"] = {"token": symbol, "total_tvl": 0.0, "confidence": 0.0}

    # Get meme coins (if SOL)
    if symbol == "SOL":
        try:
            meme_coins = sol_meme.get_meme_coins(limit=10, cache=cache)
            result["meme"] = meme_coins
        except Exception as e:
            logger.warning(f"Failed to get meme coins: {e}")
            result["meme"] = []
    else:
        result["meme"] = []

    return result
