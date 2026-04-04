"""
ETH Gas Tracker using Etherscan API.

Data source: Etherscan
"""
__all__ = ['get_gas_prices', 'get_gas_history']
import logging
import os
from typing import Optional

import requests

from tradingagents_crypto.dataflows.cache import SimpleCache

logger = logging.getLogger(__name__)

DEFAULT_TTL = 60  # 1 minute - gas prices change frequently
API_URL = "https://api.etherscan.io/api"


class EtherscanClient:
    """Client for Etherscan API."""

    def __init__(self, api_key: Optional[str] = None, cache: Optional[SimpleCache] = None):
        self.api_key = api_key or os.getenv('ETHERSCAN_API_KEY')
        self.cache = cache
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TradingAgents/1.0'
        })

    def _make_request(self, module: str, action: str, params: dict = None) -> Optional[dict]:
        """Make API request with caching."""
        if not self.api_key:
            logger.warning("Etherscan API key not configured")
            return None

        request_params = {
            'module': module,
            'action': action,
            'apikey': self.api_key,
        }
        if params:
            request_params.update(params)

        cache_key = f"etherscan:{module}:{action}:{str(params)}"

        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        try:
            response = self.session.get(API_URL, params=request_params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get('status') != '1':
                logger.warning(f"Etherscan API error: {data.get('result', 'Unknown error')}")
                return None

            if self.cache:
                self.cache.set(cache_key, data, ttl=DEFAULT_TTL)

            return data
        except requests.RequestException as e:
            logger.error(f"Etherscan API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Etherscan API error: {e}")
            return None

    def get_gas_oracle(self) -> Optional[dict]:
        """Get gas price oracle data."""
        data = self._make_request('gastracker', 'gasoracle')

        if not data or 'result' not in data:
            return None

        try:
            result = data['result']
            return {
                'safe_gas_price': float(result.get('SafeGasPrice', 0)),
                'propose_gas_price': float(result.get('ProposeGasPrice', 0)),
                'fast_gas_price': float(result.get('FastGasPrice', 0)),
                'suggest_base_fee': float(result.get('suggestBaseFee', 0)),
                'gas_used_ratio': result.get('gasUsedRatio', '').split(','),
            }
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to parse gas oracle data: {e}")
            return None


def get_gas_prices(api_key: Optional[str] = None, cache=None) -> dict:
    """
    Get current ETH gas prices from Etherscan.

    Args:
        api_key: Etherscan API key (or set ETHERSCAN_API_KEY env var)
        cache: Optional cache instance

    Returns:
        Dict with:
        - safe: float (safe gas price in gwei)
        - standard: float (standard/proposed gas price in gwei)
        - fast: float (fast gas price in gwei)
        - base_fee: float (suggested base fee in gwei)
        - classification: str ("low", "medium", "high", "extreme")
        - confidence: float
    """
    client = EtherscanClient(api_key=api_key, cache=cache)
    oracle = client.get_gas_oracle()

    if not oracle:
        return {
            'safe': 0.0,
            'standard': 0.0,
            'fast': 0.0,
            'base_fee': 0.0,
            'classification': 'unknown',
            'confidence': 0.3,
            'error': 'Failed to fetch gas prices (Etherscan API unavailable)',
            'note': 'Set ETHERSCAN_API_KEY environment variable',
        }

    # Classify gas prices
    fast = oracle['fast_gas_price']
    if fast < 20:
        classification = 'low'
    elif fast < 50:
        classification = 'medium'
    elif fast < 100:
        classification = 'high'
    else:
        classification = 'extreme'

    return {
        'safe': oracle['safe_gas_price'],
        'standard': oracle['propose_gas_price'],
        'fast': oracle['fast_gas_price'],
        'base_fee': oracle['suggest_base_fee'],
        'classification': classification,
        'confidence': 0.9,
    }


def get_gas_history(days: int = 7, api_key: Optional[str] = None, cache=None) -> list:
    """
    Get historical gas price data.

    Note: Etherscan free API doesn't provide historical gas data.
    This is a placeholder for future implementation.

    Returns:
        Empty list (placeholder)
    """
    # TODO: Implement using Etherscan Pro or alternative source
    logger.info("Historical gas data not available in free Etherscan API")
    return []
