"""
Bybit funding rate client.

Used as primary data source for:
- ETH-PERP funding rates (since Binance is blocked)
- Other perpetual funding rates

API Docs: https://bybit-exchange.github.io/docs/
Base URL: https://api.bybit.com
"""
import logging
from datetime import datetime, timezone

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from tradingagents_crypto.dataflows.hyperliquid.cache import CacheManager

logger = logging.getLogger(__name__)

DEFAULT_TTL = 300  # 5 minutes


class BybitClient:
    """Bybit API client for funding rates."""

    BASE_URL = "https://api.bybit.com"

    def __init__(self, cache: CacheManager | None = None):
        self.cache = cache or CacheManager()
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        """Make a GET request with retry."""
        url = f"{self.BASE_URL}{endpoint}"
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_funding_rate(self, symbol: str = "ETHUSDT") -> dict:
        """
        Get current funding rate for a perpetual symbol.

        Args:
            symbol: Bybit symbol, e.g., "ETHUSDT", "BTCUSDT"

        Returns:
            Dict with:
            - symbol: str
            - funding_rate: float (8h rate, e.g., 0.0001 = 0.01%)
            - annualized: float (rate * 3 * 365)
            - next_funding_time: datetime
            - confidence: 0.85 (Bybit official)
        """
        cache_key = f"bybit:funding:{symbol}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            # Bybit v5 API
            data = self._get(
                "/v5/market/tickers",
                params={"category": "linear", "symbol": symbol}
            )

            result_list = data.get("result", {}).get("list", [])
            if not result_list:
                logger.warning(f"Bybit returned empty result for {symbol}")
                return self._empty_result(symbol)

            ticker = result_list[0]

            # Funding rate is in the ticker data
            funding_rate_str = ticker.get("fundingRate", "0")
            funding_rate = float(funding_rate_str)

            # Next funding time (Unix timestamp in milliseconds)
            next_funding_ts = int(ticker.get("nextFundingTime", 0))
            next_funding_time = datetime.fromtimestamp(
                next_funding_ts / 1000, tz=timezone.utc
            ) if next_funding_ts else None

            result = {
                "symbol": symbol,
                "funding_rate": funding_rate,
                "annualized": funding_rate * 3 * 365,
                "next_funding_time": next_funding_time,
                "next_funding_str": next_funding_time.strftime("%Y-%m-%d %H:%M UTC") if next_funding_time else None,
                "confidence": 0.85,  # Bybit official exchange
            }

            self.cache.set(cache_key, result, DEFAULT_TTL)
            return result

        except Exception as e:
            logger.warning(f"BybitClient.get_funding_rate({symbol}) failed: {e}")
            return self._empty_result(symbol)

    def _empty_result(self, symbol: str) -> dict:
        """Return empty result when API fails."""
        return {
            "symbol": symbol,
            "funding_rate": 0.0,
            "annualized": 0.0,
            "next_funding_time": None,
            "next_funding_str": None,
            "confidence": 0.5,  # Lower when API fails
        }

    def get_eth_funding(self) -> dict:
        """Get ETH-USDT funding rate (convenience method)."""
        return self.get_funding_rate("ETHUSDT")

    def get_btc_funding(self) -> dict:
        """Get BTC-USDT funding rate (convenience method)."""
        return self.get_funding_rate("BTCUSDT")
