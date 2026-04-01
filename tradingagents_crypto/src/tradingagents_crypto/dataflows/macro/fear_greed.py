"""
Fear & Greed Index data.

Data source: Alternative.me API
Free, no API key required.

API: https://api.alternative.me/fng/
"""
__all__ = ['FearGreedClient', 'get_current', 'get_label_from_value', 'interpret']
import logging
from datetime import datetime, timezone

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from tradingagents_crypto.dataflows.hyperliquid.cache import CacheManager

logger = logging.getLogger(__name__)

DEFAULT_TTL = 3600  # 1 hour - Fear & Greed only updates daily


class FearGreedClient:
    """Alternative.me Fear & Greed API client."""

    BASE_URL = "https://api.alternative.me"
    ENDPOINT = "/fng/"

    def __init__(self, cache: CacheManager | None = None):
        self.cache = cache or CacheManager()
        self.session = requests.Session()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _get(self) -> dict:
        """Make a GET request with retry."""
        url = f"{self.BASE_URL}{self.ENDPOINT}"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_current(self) -> dict:
        """
        Get current Fear & Greed index.

        Returns:
            Dict with:
            - value: int (0-100)
            - label: str ("Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed")
            - timestamp: datetime
            - confidence: 0.5 (free data)
        """
        cache_key = "fear_greed:current"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            data = self._get()
            items = data.get("data", [])

            if not items:
                logger.warning("Fear & Greed API returned no data")
                return self._empty_result()

            latest = items[0]

            # Parse timestamp (milliseconds)
            ts_ms = int(latest.get("timestamp", 0)) * 1000
            dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)

            value = int(latest.get("value", 50))
            classification = latest.get("value_classification", "Neutral")

            result = {
                "value": value,
                "label": classification,
                "timestamp": dt,
                "update_time": dt.strftime("%Y-%m-%d %H:%M UTC"),
                "confidence": 0.5,  # Free data, low confidence
            }

            self.cache.set(cache_key, result, DEFAULT_TTL)
            return result

        except Exception as e:
            logger.warning(f"FearGreedClient.get_current failed: {e}")
            return self._empty_result()

    def _empty_result(self) -> dict:
        """Return empty result when API fails."""
        return {
            "value": 50,
            "label": "Neutral",
            "timestamp": None,
            "update_time": None,
            "confidence": 0.3,  # Lower when API fails
        }

    def get_label_from_value(self, value: int) -> str:
        """
        Get label from numeric value.

        Args:
            value: 0-100

        Returns:
            Label string
        """
        if value <= 25:
            return "Extreme Fear"
        elif value <= 50:
            return "Fear"
        elif value <= 75:
            return "Greed"
        else:
            return "Extreme Greed"

    def interpret(self) -> dict:
        """
        Get interpreted Fear & Greed with trading signal.

        Returns:
            Dict with interpretation for trading
        """
        data = self.get_current()
        value = data.get("value", 50)

        # Trading interpretation
        if value <= 25:
            signal = "buy_opportunity"
            reason = "Extreme Fear often indicates market bottom"
        elif value <= 40:
            signal = "cautious_buy"
            reason = "Fear may indicate oversold conditions"
        elif value <= 60:
            signal = "neutral"
            reason = "Market in neutral zone"
        elif value <= 75:
            signal = "cautious_sell"
            reason = "Greed may indicate overbought conditions"
        else:
            signal = "sell_opportunity"
            reason = "Extreme Greed often indicates market top"

        return {
            **data,
            "signal": signal,
            "reason": reason,
        }
