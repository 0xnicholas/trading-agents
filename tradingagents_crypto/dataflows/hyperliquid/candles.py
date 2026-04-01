"""
Hyperliquid candlestick data.

High-level functions for getting and caching candle data.
"""
import logging
from typing import Annotated

import pandas as pd

from .api import HLClient
from .cache import CacheManager
from .utils import calc_time_range, now_ms

logger = logging.getLogger(__name__)

# Default cache TTL in seconds
DEFAULT_TTL = 3600  # 1 hour


def get_candles(
    symbol: str,
    interval: str,
    days: int = 7,
    client: HLClient | None = None,
    cache: CacheManager | None = None,
    ttl: int = DEFAULT_TTL,
) -> pd.DataFrame:
    """
    Get candlestick data for a symbol.

    Args:
        symbol: Coin name (e.g., "BTC", "ETH")
        interval: "1h", "4h", or "1d"
        days: Number of days to look back
        client: Optional HLClient instance (creates default if None)
        cache: Optional CacheManager instance (creates default if None)
        ttl: Cache TTL in seconds (default: 3600)

    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume, n_trades
        Sorted by timestamp ascending.
        timestamp is Unix seconds (int).
    """
    if client is None:
        client = HLClient()
    if cache is None:
        cache = CacheManager()

    start_ms, end_ms = calc_time_range(interval, days)
    cache_key = cache.candle_key(symbol, interval, start_ms, end_ms)

    # Check cache first
    cached = cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Cache hit for {cache_key}")
        return pd.DataFrame(cached)

    # Fetch from API
    logger.debug(f"Fetching {symbol} {interval} from API")
    raw_candles = client.get_candles(symbol, interval, start_ms, end_ms)

    # Parse into DataFrame
    records = []
    for c in raw_candles:
        # SDK returns: T(ms), o, h, l, c, v, n
        # Convert timestamp to seconds
        ts_sec = c.get("t", c.get("T", 0)) // 1000
        records.append({
            "timestamp": ts_sec,
            "open": float(c["o"]) if c.get("o") else None,
            "high": float(c["h"]) if c.get("h") else None,
            "low": float(c["l"]) if c.get("l") else None,
            "close": float(c["c"]) if c.get("c") else None,
            "volume": float(c["v"]) if c.get("v") else None,
            "n_trades": int(c.get("n", 0)),
        })

    df = pd.DataFrame(records)
    df = df.dropna(subset=["close"])  # Remove rows with no close price
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Cache the result
    cache.set(cache_key, df.to_dict("records"), ttl)

    return df


def get_candles_batch(
    symbols: list[str],
    interval: str,
    days: int = 7,
    client: HLClient | None = None,
    cache: CacheManager | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Get candlestick data for multiple symbols.

    Args:
        symbols: List of coin names
        interval: "1h", "4h", or "1d"
        days: Number of days to look back
        client: Optional HLClient instance
        cache: Optional CacheManager instance

    Returns:
        Dict mapping symbol -> DataFrame
    """
    results = {}
    for symbol in symbols:
        try:
            results[symbol] = get_candles(
                symbol, interval, days, client, cache
            )
        except Exception as e:
            logger.warning(f"Failed to get candles for {symbol}: {e}")
            results[symbol] = pd.DataFrame()
    return results
