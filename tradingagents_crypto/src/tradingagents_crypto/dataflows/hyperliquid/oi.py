"""
Hyperliquid open interest data.

High-level functions for OI and asset context data.
"""
__all__ = ['get_open_interest', 'get_all_open_interest']
import logging
from .api import HLClient
from .cache import CacheManager

logger = logging.getLogger(__name__)

DEFAULT_TTL = 300  # 5 minutes


def get_open_interest(
    symbol: str,
    client: HLClient | None = None,
    cache: CacheManager | None = None,
) -> dict:
    """
    Get open interest data for a symbol.

    Args:
        symbol: Coin name (e.g., "BTC", "ETH")
        client: Optional HLClient instance
        cache: Optional CacheManager instance

    Returns:
        Dict with keys:
        - open_interest_usd: Open interest in USD
        - prev_day_px: Previous day close price
        - mark_px: Mark price
        - oracle_px: Oracle price
        - funding: Current funding rate (8h)
        - day_ntl_vlm: 24h notional volume
    """
    if client is None:
        client = HLClient()
    if cache is None:
        cache = CacheManager()

    cache_key = cache.oi_key(symbol)

    # Check cache
    cached = cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Cache hit for OI: {cache_key}")
        return cached

    # Get meta and asset contexts
    meta, asset_ctxs = client.get_meta_and_asset_ctxs()

    # Find index of symbol in universe
    universe = meta.get("universe", [])
    idx = None
    for i, coin_meta in enumerate(universe):
        if coin_meta.get("name") == symbol:
            idx = i
            break

    if idx is None or idx >= len(asset_ctxs):
        logger.warning(f"Symbol {symbol} not found in universe")
        return _empty_oi(symbol)

    ctx = asset_ctxs[idx]

    # Handle both dict and non-dict ctx
    if isinstance(ctx, dict):
        open_interest = float(ctx.get("openInterest", 0) or 0)
        prev_day_px = float(ctx.get("prevDayPx", 0) or 0)
        mark_px = float(ctx.get("markPx", 0) or 0)
        oracle_px = float(ctx.get("oraclePx", 0) or 0)
        funding = float(ctx.get("funding", 0) or 0)
        day_ntl_vlm = float(ctx.get("dayNtlVlm", 0) or 0)
    else:
        open_interest = 0.0
        prev_day_px = 0.0
        mark_px = 0.0
        oracle_px = 0.0
        funding = 0.0
        day_ntl_vlm = 0.0

    result = {
        "open_interest_usd": open_interest,
        "prev_day_px": prev_day_px,
        "mark_px": mark_px,
        "oracle_px": oracle_px,
        "funding": funding,
        "day_ntl_vlm": day_ntl_vlm,
    }

    cache.set(cache_key, result, DEFAULT_TTL)
    return result


def _empty_oi(symbol: str) -> dict:
    """Return empty OI dict for unknown symbols."""
    return {
        "open_interest_usd": 0.0,
        "prev_day_px": 0.0,
        "mark_px": 0.0,
        "oracle_px": 0.0,
        "funding": 0.0,
        "day_ntl_vlm": 0.0,
    }


def get_all_open_interest(
    client: HLClient | None = None,
) -> dict[str, dict]:
    """
    Get open interest for all symbols.

    Args:
        client: Optional HLClient instance

    Returns:
        Dict mapping symbol -> OI dict
    """
    if client is None:
        client = HLClient()

    meta, asset_ctxs = client.get_meta_and_asset_ctxs()
    universe = meta.get("universe", [])

    results = {}
    for i, coin_meta in enumerate(universe):
        symbol = coin_meta.get("name")
        if symbol and i < len(asset_ctxs):
            ctx = asset_ctxs[i]
            if isinstance(ctx, dict):
                results[symbol] = {
                    "open_interest_usd": float(ctx.get("openInterest", 0) or 0),
                    "mark_px": float(ctx.get("markPx", 0) or 0),
                    "funding": float(ctx.get("funding", 0) or 0),
                }
    return results
