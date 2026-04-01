"""
Ethereum funding rate data.

Data source: Bybit (primary, since Binance is blocked)
"""
import logging

from tradingagents_crypto.dataflows.bybit import BybitClient

logger = logging.getLogger(__name__)

DEFAULT_TTL = 300  # 5 minutes


def get_binance_funding(
    cache=None,
) -> dict:
    """
    Get ETH-PERP funding rate from Bybit.

    Note: Named "binance" for compatibility, actual source is Bybit.

    Returns:
        Dict with:
        - symbol: str ("ETHUSDT")
        - funding_rate: float (8h rate)
        - annualized: float (rate * 3 * 365)
        - next_funding_time: datetime or None
        - next_funding_str: str
        - confidence: float (0.85 for Bybit)
    """
    client = BybitClient(cache=cache)
    return client.get_eth_funding()


def get_eth_funding_rate(cache=None) -> dict:
    """
    Alias for get_binance_funding.

    Returns ETH-PERP funding rate.
    """
    return get_binance_funding(cache=cache)
