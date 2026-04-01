"""
Hyperliquid funding rate data.

High-level functions for funding rate data.
"""
__all__ = ['get_current_funding', 'get_funding_history']
import logging
from .api import HLClient
from .cache import CacheManager
from .utils import calc_time_range, now_ms

logger = logging.getLogger(__name__)

DEFAULT_TTL = 300  # 5 minutes


def get_current_funding(
    symbol: str,
    client: HLClient | None = None,
    cache: CacheManager | None = None,
) -> dict:
    """
    Get current funding rate for a symbol.

    Args:
        symbol: Coin name (e.g., "BTC")
        client: Optional HLClient instance
        cache: Optional CacheManager instance

    Returns:
        Dict with keys:
        - funding_rate: 8h rate (e.g., 0.0001)
        - annualized: annualized rate (rate * 3 * 365)
        - premium: premium value
        - time: Unix seconds
    """
    if client is None:
        client = HLClient()
    if cache is None:
        cache = CacheManager()

    cache_key = cache.funding_key(symbol)

    # Check cache
    cached = cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Cache hit for funding: {cache_key}")
        return cached

    # Get last 24 hours of funding history
    end_ms = now_ms()
    start_ms = end_ms - 86400 * 1000  # 24h
    history = client.get_funding_history(symbol, start_ms, end_ms)

    if not history:
        return {
            "funding_rate": 0.0,
            "annualized": 0.0,
            "premium": 0.0,
            "time": end_ms // 1000,
        }

    # Get the latest entry
    latest = history[-1]
    rate = float(latest.get("fundingRate", 0))
    premium = float(latest.get("premium", 0))
    time_sec = int(latest.get("time", 0)) // 1000  # ms to sec

    result = {
        "funding_rate": rate,
        "annualized": rate * 3 * 365,  # 3 settlements per day
        "premium": premium,
        "time": time_sec,
    }

    cache.set(cache_key, result, DEFAULT_TTL)
    return result


def get_funding_history(
    symbol: str,
    days: int = 30,
    client: HLClient | None = None,
) -> list[dict]:
    """
    Get funding rate history.

    Args:
        symbol: Coin name
        days: Number of days to look back
        client: Optional HLClient instance

    Returns:
        List of funding records
    """
    if client is None:
        client = HLClient()

    end_ms = now_ms()
    start_ms = end_ms - days * 86400 * 1000
    return client.get_funding_history(symbol, start_ms, end_ms)
