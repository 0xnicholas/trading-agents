"""
Macro data layer - unified entry point.

Aggregates all macro market data:
- BTC Dominance
- Fear & Greed
- Stablecoin Flow
- Cross-chain correlations
"""
__all__ = ['_safe_get', 'get_macro_data']
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
    result["btc_dominance"] = _safe_get(
        lambda: btc_dominance.get_btc_dominance(cache=cache),
        "BTC dominance",
        {"btc_dominance": 0.0, "confidence": 0.0},
    )

    # Fear & Greed
    result["fear_greed"] = _safe_get(
        lambda: fear_greed.get_current(cache=cache),
        "Fear & Greed",
        {"value": 50, "label": "Neutral", "confidence": 0.0},
    )

    # Stablecoin Flow
    result["stablecoin_flow"] = _safe_get(
        lambda: stablecoin_flow.get_stablecoin_flow(cache=cache),
        "Stablecoin flow",
        {"total_supply": 0.0, "confidence": 0.0},
    )

    # Correlation
    result["correlation"] = _safe_get(
        lambda: correlation.get_correlations(cache=cache),
        "Correlations",
        {"btc_eth_corr_7d": 0.0, "btc_sol_corr_7d": 0.0, "confidence": 0.0},
    )

    return result
