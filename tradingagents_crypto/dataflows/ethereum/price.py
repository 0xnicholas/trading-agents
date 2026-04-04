"""
Ethereum price data module.

Data source: CoinGecko API (primary), CoinCap (fallback)
Provides ETH price data with caching and deviation checking.
"""
from __future__ import annotations

__all__ = ["get_eth_price", "check_price_deviation"]

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import aiohttp
import pandas as pd
from cachetools import TTLCache

logger = logging.getLogger(__name__)

# Constants
DEFAULT_TTL = 300  # 5 minutes cache
CACHE_MAXSIZE = 100

# API endpoints
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
COINCAP_API_URL = "https://api.coincap.io/v2"

# Cache instances
_price_cache: TTLCache = TTLCache(maxsize=CACHE_MAXSIZE, ttl=DEFAULT_TTL)
_history_cache: TTLCache = TTLCache(maxsize=CACHE_MAXSIZE, ttl=DEFAULT_TTL)


async def get_eth_price(days: int = 7) -> pd.DataFrame:
    """
    Get ETH price history from CoinGecko API.

    T2.1.1: ETH price data with OHLCV format.

    Args:
        days: Number of days of history (default: 7, max: 365)

    Returns:
        pd.DataFrame with columns:
        - timestamp: datetime
        - price: float (USD)
        - market_cap: float
        - volume: float (24h)
        - confidence: float (0.75)

    Raises:
        ValueError: If days parameter is invalid
    """
    if not isinstance(days, int) or days < 1 or days > 365:
        raise ValueError("days must be between 1 and 365")

    cache_key = f"eth_price_history:{days}"
    cached = _price_cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Cache hit for {cache_key}")
        return cached

    try:
        df = await _fetch_coingecko_price_history(days)
        _price_cache[cache_key] = df
        return df
    except Exception as e:
        logger.warning(f"CoinGecko failed: {e}, trying CoinCap fallback")
        try:
            df = await _fetch_coincap_price_history(days)
            _price_cache[cache_key] = df
            return df
        except Exception as e2:
            logger.error(f"Both price sources failed: {e2}")
            return _empty_price_df()


async def _fetch_coingecko_price_history(days: int) -> pd.DataFrame:
    """Fetch ETH price history from CoinGecko."""
    url = f"{COINGECKO_API_URL}/coins/ethereum/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "daily" if days > 1 else "hourly",
    }

    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params) as response:
            if response.status == 429:
                logger.warning("CoinGecko rate limit hit, waiting...")
                await asyncio.sleep(2)
                raise aiohttp.ClientError("Rate limited")
            response.raise_for_status()
            data = await response.json()

    # Parse response
    prices = data.get("prices", [])
    market_caps = data.get("market_caps", [])
    volumes = data.get("total_volumes", [])

    if not prices:
        raise ValueError("Empty price data from CoinGecko")

    # Build DataFrame
    records = []
    for i, (ts, price) in enumerate(prices):
        timestamp = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        market_cap = market_caps[i][1] if i < len(market_caps) else None
        volume = volumes[i][1] if i < len(volumes) else None

        records.append({
            "timestamp": timestamp,
            "price": float(price),
            "market_cap": float(market_cap) if market_cap else None,
            "volume": float(volume) if volume else None,
            "confidence": 0.75,
        })

    df = pd.DataFrame(records)
    logger.info(f"Fetched {len(df)} ETH price records from CoinGecko")
    return df


async def _fetch_coincap_price_history(days: int) -> pd.DataFrame:
    """Fetch ETH price history from CoinCap (fallback)."""
    # CoinCap uses interval-based history
    interval = "d1" if days > 1 else "h1"
    end = int(datetime.now(timezone.utc).timestamp() * 1000)
    start = end - (days * 24 * 60 * 60 * 1000)

    url = f"{COINCAP_API_URL}/assets/ethereum/history"
    params = {
        "interval": interval,
        "start": start,
        "end": end,
    }

    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            data = await response.json()

    history = data.get("data", [])
    if not history:
        raise ValueError("Empty price data from CoinCap")

    records = []
    for item in history:
        timestamp = datetime.fromtimestamp(
            int(item.get("time", 0)) / 1000, tz=timezone.utc
        )
        records.append({
            "timestamp": timestamp,
            "price": float(item.get("priceUsd", 0)),
            "market_cap": None,  # CoinCap doesn't provide in history
            "volume": None,
            "confidence": 0.70,  # Slightly lower for fallback
        })

    df = pd.DataFrame(records)
    logger.info(f"Fetched {len(df)} ETH price records from CoinCap")
    return df


def _empty_price_df() -> pd.DataFrame:
    """Return empty DataFrame with correct schema."""
    return pd.DataFrame({
        "timestamp": pd.Series(dtype="datetime64[ns, UTC]"),
        "price": pd.Series(dtype="float64"),
        "market_cap": pd.Series(dtype="float64"),
        "volume": pd.Series(dtype="float64"),
        "confidence": pd.Series(dtype="float64"),
    })


def check_price_deviation(eth_price: float, hl_mark_px: float) -> dict[str, Any]:
    """
    Check deviation between external ETH price and Hyperliquid mark price.

    T2.1.2: Price deviation detection for arbitrage signals.

    Args:
        eth_price: External ETH price (e.g., from CoinGecko)
        hl_mark_px: Hyperliquid mark price

    Returns:
        Dict with:
        - deviation_pct: float (absolute percentage deviation)
        - deviation_sign: int (1 if external > HL, -1 if external < HL, 0 if equal)
        - warning: bool (True if deviation > 1%)
        - arbitrage_signal: str ("buy_hl", "sell_hl", or "neutral")
        - confidence: float (0.75 if no warning, 0.65 if warning)

    Raises:
        ValueError: If prices are negative or zero
    """
    if eth_price <= 0 or hl_mark_px <= 0:
        raise ValueError("Prices must be positive")

    # Calculate deviation
    deviation_pct = abs((eth_price - hl_mark_px) / hl_mark_px * 100)
    deviation_sign = 0
    if eth_price > hl_mark_px:
        deviation_sign = 1
    elif eth_price < hl_mark_px:
        deviation_sign = -1

    # Warning threshold: 1%
    warning = deviation_pct > 1.0

    # Arbitrage signal
    if deviation_pct > 0.5:  # 0.5% threshold for signal
        if deviation_sign > 0:
            arbitrage_signal = "buy_hl"  # HL is cheaper
        else:
            arbitrage_signal = "sell_hl"  # HL is more expensive
    else:
        arbitrage_signal = "neutral"

    return {
        "deviation_pct": round(deviation_pct, 4),
        "deviation_sign": deviation_sign,
        "warning": warning,
        "arbitrage_signal": arbitrage_signal,
        "confidence": 0.65 if warning else 0.75,
    }


async def get_current_eth_price() -> dict[str, Any]:
    """
    Get current ETH price (convenience function).

    Returns:
        Dict with current price data and confidence
    """
    cache_key = "eth_current_price"
    cached = _price_cache.get(cache_key)
    if cached is not None:
        return cached

    url = f"{COINGECKO_API_URL}/simple/price"
    params = {
        "ids": "ethereum",
        "vs_currencies": "usd",
        "include_market_cap": "true",
        "include_24hr_vol": "true",
        "include_24hr_change": "true",
    }

    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

        eth_data = data.get("ethereum", {})
        result = {
            "price_usd": float(eth_data.get("usd", 0)),
            "market_cap": float(eth_data.get("usd_market_cap", 0)),
            "volume_24h": float(eth_data.get("usd_24h_vol", 0)),
            "change_24h_pct": float(eth_data.get("usd_24h_change", 0)),
            "confidence": 0.75,
            "timestamp": datetime.now(timezone.utc),
        }
        _price_cache[cache_key] = result
        return result

    except Exception as e:
        logger.error(f"Failed to get current ETH price: {e}")
        return {
            "price_usd": 0.0,
            "market_cap": 0.0,
            "volume_24h": 0.0,
            "change_24h_pct": 0.0,
            "confidence": 0.0,
            "timestamp": datetime.now(timezone.utc),
            "error": str(e),
        }
