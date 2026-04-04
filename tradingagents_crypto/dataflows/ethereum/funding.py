"""
Ethereum funding rate module.

Data source: Binance Futures API (primary), Bybit (fallback)
Provides ETH-PERP funding rate data with caching.
"""
from __future__ import annotations

__all__ = ["get_binance_funding", "get_eth_funding_rate"]

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import aiohttp
from cachetools import TTLCache

logger = logging.getLogger(__name__)

# Constants
DEFAULT_TTL = 300  # 5 minutes cache
CACHE_MAXSIZE = 100

# API endpoints
BINANCE_FAPI_URL = "https://fapi.binance.com"
BYBIT_API_URL = "https://api.bybit.com"

# Cache instance
_funding_cache: TTLCache = TTLCache(maxsize=CACHE_MAXSIZE, ttl=DEFAULT_TTL)


async def get_binance_funding(symbol: str = "ETHUSDT") -> dict[str, Any]:
    """
    Get ETH-PERP funding rate from Binance Futures API.

    T2.1.4: Funding rate data for funding arbitrage strategy.

    Args:
        symbol: Trading pair symbol (default: "ETHUSDT")

    Returns:
        Dict with:
        - symbol: str (trading pair)
        - funding_rate: float (8-hour funding rate, e.g., 0.0001 = 0.01%)
        - annualized: float (rate * 3 * 365, approximate APY)
        - next_funding_time: datetime or None
        - next_funding_str: str (formatted time string)
        - confidence: float (0.85 for Binance)
        - timestamp: datetime

    Raises:
        ValueError: If symbol is invalid
    """
    if not symbol or not isinstance(symbol, str):
        raise ValueError("symbol must be a non-empty string")

    cache_key = f"binance_funding:{symbol}"
    cached = _funding_cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Cache hit for {cache_key}")
        return cached

    try:
        result = await _fetch_binance_funding(symbol)
        _funding_cache[cache_key] = result
        return result
    except Exception as e:
        logger.warning(f"Binance funding failed: {e}, trying Bybit fallback")
        try:
            result = await _fetch_bybit_funding(symbol)
            _funding_cache[cache_key] = result
            return result
        except Exception as e2:
            logger.error(f"Both funding sources failed: {e2}")
            return _empty_funding_result(symbol)


async def _fetch_binance_funding(symbol: str) -> dict[str, Any]:
    """Fetch funding rate from Binance Futures."""
    url = f"{BINANCE_FAPI_URL}/fapi/v1/premiumIndex"
    params = {"symbol": symbol}

    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params) as response:
            if response.status == 429:
                logger.warning("Binance rate limit hit, waiting...")
                await asyncio.sleep(2)
                raise aiohttp.ClientError("Rate limited")
            response.raise_for_status()
            data = await response.json()

    # Parse response
    funding_rate = float(data.get("lastFundingRate", 0))
    next_funding_ts = data.get("nextFundingTime", 0)

    next_funding_time = None
    next_funding_str = None
    if next_funding_ts:
        next_funding_time = datetime.fromtimestamp(
            next_funding_ts / 1000, tz=timezone.utc
        )
        next_funding_str = next_funding_time.strftime("%Y-%m-%d %H:%M UTC")

    # Calculate annualized rate (8h * 3 * 365 = 1095 periods/year)
    annualized = funding_rate * 3 * 365

    result = {
        "symbol": symbol,
        "funding_rate": funding_rate,
        "annualized": round(annualized, 6),
        "mark_price": float(data.get("markPrice", 0)),
        "index_price": float(data.get("indexPrice", 0)),
        "next_funding_time": next_funding_time,
        "next_funding_str": next_funding_str,
        "confidence": 0.85,  # Binance official exchange
        "timestamp": datetime.now(timezone.utc),
        "source": "binance",
    }

    logger.info(
        f"Binance funding rate for {symbol}: {funding_rate:.6f} "
        f"(annualized: {annualized:.2%})"
    )
    return result


async def _fetch_bybit_funding(symbol: str) -> dict[str, Any]:
    """Fetch funding rate from Bybit (fallback)."""
    url = f"{BYBIT_API_URL}/v5/market/tickers"
    params = {
        "category": "linear",
        "symbol": symbol,
    }

    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            data = await response.json()

    result_list = data.get("result", {}).get("list", [])
    if not result_list:
        raise ValueError(f"Bybit returned empty result for {symbol}")

    ticker = result_list[0]
    funding_rate = float(ticker.get("fundingRate", 0))
    next_funding_ts = int(ticker.get("nextFundingTime", 0))

    next_funding_time = None
    next_funding_str = None
    if next_funding_ts:
        next_funding_time = datetime.fromtimestamp(
            next_funding_ts / 1000, tz=timezone.utc
        )
        next_funding_str = next_funding_time.strftime("%Y-%m-%d %H:%M UTC")

    annualized = funding_rate * 3 * 365

    result = {
        "symbol": symbol,
        "funding_rate": funding_rate,
        "annualized": round(annualized, 6),
        "mark_price": float(ticker.get("markPrice", 0)),
        "index_price": float(ticker.get("indexPrice", 0)),
        "next_funding_time": next_funding_time,
        "next_funding_str": next_funding_str,
        "confidence": 0.80,  # Slightly lower for fallback
        "timestamp": datetime.now(timezone.utc),
        "source": "bybit",
    }

    logger.info(
        f"Bybit funding rate for {symbol}: {funding_rate:.6f} "
        f"(annualized: {annualized:.2%})"
    )
    return result


def _empty_funding_result(symbol: str) -> dict[str, Any]:
    """Return empty result when all sources fail."""
    return {
        "symbol": symbol,
        "funding_rate": 0.0,
        "annualized": 0.0,
        "mark_price": 0.0,
        "index_price": 0.0,
        "next_funding_time": None,
        "next_funding_str": None,
        "confidence": 0.0,
        "timestamp": datetime.now(timezone.utc),
        "source": "none",
        "error": "All funding sources failed",
    }


async def get_eth_funding_rate() -> dict[str, Any]:
    """
    Get ETH-USDT funding rate (convenience function).

    Alias for get_binance_funding with ETHUSDT symbol.

    Returns:
        Dict with funding rate data and confidence
    """
    return await get_binance_funding("ETHUSDT")


async def get_funding_history(
    symbol: str = "ETHUSDT",
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    Get historical funding rates from Binance.

    T2.1.5: Historical funding data for trend analysis.

    Args:
        symbol: Trading pair symbol
        limit: Number of records (max 1000)

    Returns:
        List of funding rate records with timestamp
    """
    if limit < 1 or limit > 1000:
        raise ValueError("limit must be between 1 and 1000")

    cache_key = f"binance_funding_history:{symbol}:{limit}"
    cached = _funding_cache.get(cache_key)
    if cached is not None:
        return cached

    url = f"{BINANCE_FAPI_URL}/fapi/v1/fundingRate"
    params = {
        "symbol": symbol,
        "limit": limit,
    }

    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

        records = []
        for item in data:
            funding_time = datetime.fromtimestamp(
                item.get("fundingTime", 0) / 1000, tz=timezone.utc
            )
            records.append({
                "symbol": item.get("symbol", symbol),
                "funding_rate": float(item.get("fundingRate", 0)),
                "funding_time": funding_time,
                "funding_time_str": funding_time.strftime("%Y-%m-%d %H:%M UTC"),
                "confidence": 0.85,
            })

        _funding_cache[cache_key] = records
        logger.info(f"Fetched {len(records)} funding history records for {symbol}")
        return records

    except Exception as e:
        logger.error(f"Failed to get funding history: {e}")
        return []
