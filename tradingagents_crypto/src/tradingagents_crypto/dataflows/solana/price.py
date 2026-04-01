"""
Solana price data.

Data source: CoinCap.io (primary, since Jupiter is blocked)
"""
__all__ = ['get_sol_price']
import logging

from tradingagents_crypto.dataflows.coincap import CoinCapClient

logger = logging.getLogger(__name__)

DEFAULT_TTL = 300  # 5 minutes


def get_sol_price(
    cache=None,
) -> dict:
    """
    Get SOL price and related data from CoinCap.

    Returns:
        Dict with:
        - price_usd: float
        - change_24h_pct: float
        - market_cap: float
        - volume_24h: float
        - rank: int
        - confidence: float (0.8 for CoinCap SOL)
    """
    client = CoinCapClient(cache=cache)
    return client.get_sol_price()
