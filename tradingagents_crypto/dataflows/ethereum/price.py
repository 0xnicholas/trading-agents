"""
Ethereum price data.

Data source: CoinCap.io (primary, since CoinGecko is blocked)
"""
__all__ = ['get_eth_price', 'check_price_deviation']
import logging
from typing import Annotated

from tradingagents_crypto.dataflows.coincap import CoinCapClient

logger = logging.getLogger(__name__)

DEFAULT_TTL = 300  # 5 minutes


def get_eth_price(
    cache=None,
) -> dict:
    """
    Get ETH price and related data from CoinCap.

    Returns:
        Dict with:
        - price_usd: float
        - change_24h_pct: float
        - market_cap: float
        - volume_24h: float
        - rank: int
        - confidence: float (0.75 for CoinCap)
    """
    client = CoinCapClient(cache=cache)
    return client.get_eth_price()


def check_price_deviation(
    eth_price: float,
    hl_mark_px: float,
) -> dict:
    """
    Check deviation between CoinCap ETH price and Hyperliquid mark price.

    Args:
        eth_price: CoinCap ETH price in USD
        hl_mark_px: Hyperliquid mark price in USD

    Returns:
        Dict with:
        - deviation_pct: float (absolute % deviation)
        - warning: bool (True if > 1%)
        - confidence_adjustment: float (-0.1 if warning)
    """
    if eth_price <= 0 or hl_mark_px <= 0:
        return {
            "deviation_pct": 0.0,
            "warning": False,
            "confidence_adjustment": 0.0,
        }

    deviation_pct = abs((eth_price - hl_mark_px) / hl_mark_px * 100)

    return {
        "deviation_pct": round(deviation_pct, 4),
        "warning": deviation_pct > 1.0,
        "confidence_adjustment": -0.1 if deviation_pct > 1.0 else 0.0,
    }
