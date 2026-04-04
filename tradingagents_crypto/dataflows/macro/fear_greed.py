"""
Fear & Greed Index data flow.

Data source: Alternative.me
"""
__all__ = ['get_fear_greed_index', 'get_fear_greed_history']
import logging
import requests
from typing import Optional

from tradingagents_crypto.dataflows.cache import SimpleCache

logger = logging.getLogger(__name__)

DEFAULT_TTL = 3600  # 1 hour - index updates daily
API_URL = "https://api.alternative.me/fng/"


class FearGreedClient:
    """Client for Fear & Greed Index API."""

    def __init__(self, cache: Optional[SimpleCache] = None):
        self.cache = cache
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TradingAgents/1.0'
        })

    def _make_request(self, params: dict = None) -> Optional[dict]:
        """Make API request with caching."""
        cache_key = f"fng:{str(params)}"

        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        try:
            response = self.session.get(API_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if self.cache:
                self.cache.set(cache_key, data, ttl=DEFAULT_TTL)

            return data
        except requests.RequestException as e:
            logger.error(f"Fear & Greed API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Fear & Greed API error: {e}")
            return None

    def get_current(self) -> Optional[dict]:
        """Get current Fear & Greed Index."""
        data = self._make_request()

        if not data or 'data' not in data or not data['data']:
            return None

        try:
            item = data['data'][0]
            return {
                'value': int(item['value']),
                'value_classification': item['value_classification'],
                'timestamp': int(item['timestamp']),
                'time_until_update': item.get('time_until_update'),
            }
        except (KeyError, ValueError, IndexError) as e:
            logger.error(f"Failed to parse Fear & Greed data: {e}")
            return None

    def get_history(self, limit: int = 30) -> list:
        """Get historical Fear & Greed Index data."""
        params = {'limit': limit}
        data = self._make_request(params)

        if not data or 'data' not in data:
            return []

        try:
            history = []
            for item in data['data']:
                history.append({
                    'value': int(item['value']),
                    'value_classification': item['value_classification'],
                    'timestamp': int(item['timestamp']),
                    'date': item.get('timestamp'),  # Human-readable date
                })
            return history
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to parse Fear & Greed history: {e}")
            return []


def get_fear_greed_index(cache=None) -> dict:
    """
    Get current Fear & Greed Index with classification.

    Returns:
        Dict with:
        - value: int (0-100)
        - classification: str ("Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed")
        - trend: str ("improving", "worsening", "stable")
        - confidence: float (0.9)
    """
    client = FearGreedClient(cache=cache)
    current = client.get_current()

    if not current:
        return {
            'value': 50,
            'classification': 'unknown',
            'trend': 'unknown',
            'confidence': 0.3,
            'error': 'Failed to fetch Fear & Greed Index',
        }

    # Get history for trend calculation
    history = client.get_history(limit=7)

    trend = 'stable'
    if len(history) >= 2:
        recent_values = [h['value'] for h in history[:3]]
        older_values = [h['value'] for h in history[3:7]]

        if recent_values and older_values:
            recent_avg = sum(recent_values) / len(recent_values)
            older_avg = sum(older_values) / len(older_values)

            diff = recent_avg - older_avg
            if diff > 5:
                trend = 'improving'
            elif diff < -5:
                trend = 'worsening'

    return {
        'value': current['value'],
        'classification': current['value_classification'],
        'trend': trend,
        'confidence': 0.9,
        'timestamp': current['timestamp'],
    }


def get_fear_greed_history(days: int = 30, cache=None) -> list:
    """
    Get historical Fear & Greed Index values.

    Args:
        days: Number of days of history (max 365)
        cache: Optional cache instance

    Returns:
        List of dicts with value and date
    """
    client = FearGreedClient(cache=cache)
    return client.get_history(limit=min(days, 365))
