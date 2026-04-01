"""
Macro data layer - unified entry point.

Aggregates all macro market data:
- BTC Dominance
- Fear & Greed
- Stablecoin Flow
- Cross-chain correlations
"""
import logging
from datetime import datetime, timezone

from tradingagents_crypto.dataflows.hyperliquid.cache import CacheManager

logger = logging.getLogger(__name__)


def get_macro_data(
    use_cache: bool = True,
) -> dict:
    """
    Get comprehensive macro data from all sources.

    Returns:
        Dict with:
        - btc_dominance: dict
        - fear_greed: dict
        - stablecoin_flow: dict
        - correlation: dict
        - timestamp: datetime
    """
    cache = CacheManager() if use_cache else None

    # Import here to avoid circular imports
    from . import btc_dominance
    from . import fear_greed
    from . import stablecoin_flow
    from . import correlation

    result = {
        "timestamp": datetime.now(timezone.utc),
    }

    # BTC Dominance
    try:
        result["btc_dominance"] = btc_dominance.get_btc_dominance(cache=cache)
    except Exception as e:
        logger.warning(f"Failed to get BTC dominance: {e}")
        result["btc_dominance"] = {"btc_dominance": 0.0, "confidence": 0.0}

    # Fear & Greed
    try:
        result["fear_greed"] = fear_greed.get_current(cache=cache)
    except Exception as e:
        logger.warning(f"Failed to get Fear & Greed: {e}")
        result["fear_greed"] = {"value": 50, "label": "Neutral", "confidence": 0.0}

    # Stablecoin Flow
    try:
        result["stablecoin_flow"] = stablecoin_flow.get_stablecoin_flow(cache=cache)
    except Exception as e:
        logger.warning(f"Failed to get stablecoin flow: {e}")
        result["stablecoin_flow"] = {"total_supply": 0.0, "confidence": 0.0}

    # Correlation
    try:
        result["correlation"] = correlation.get_correlations(cache=cache)
    except Exception as e:
        logger.warning(f"Failed to get correlations: {e}")
        result["correlation"] = {"btc_eth_corr_7d": 0.0, "btc_sol_corr_7d": 0.0, "confidence": 0.0}

    return result
