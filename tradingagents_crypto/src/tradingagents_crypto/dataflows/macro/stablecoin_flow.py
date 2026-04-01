"""
Stablecoin Flow data.

Data sources:
- CoinCap: USDT/USDC supply
- Note: Etherscan is blocked
"""
__all__ = ['get_stablecoin_flow']
import logging

from tradingagents_crypto.dataflows.coincap import CoinCapClient

logger = logging.getLogger(__name__)

DEFAULT_TTL = 300  # 5 minutes


def get_stablecoin_flow(cache=None) -> dict:
    """
    Get stablecoin flow data from CoinCap.

    Returns:
        Dict with:
        - tether_supply: float
        - usd_coin_supply: float
        - total_supply: float
        - change_24h_pct: float
        - verdict: str
        - confidence: float (0.5, approximation only)
    """
    client = CoinCapClient(cache=cache)
    data = client.get_stablecoin_supplies()

    total = data.get("total_supply", 0)
    tether_change = data.get("tether_change_24h", 0)

    # Determine verdict based on change
    if tether_change > 1.0:
        verdict = "Significant inflow, bullish signal"
    elif tether_change > 0.1:
        verdict = "Mild inflow, slight bullish"
    elif tether_change < -1.0:
        verdict = "Significant outflow, bearish signal"
    elif tether_change < -0.1:
        verdict = "Mild outflow, slight bearish"
    else:
        verdict = "Stable flow, neutral"

    return {
        "tether_supply": data.get("tether_supply", 0),
        "usd_coin_supply": data.get("usd_coin_supply", 0),
        "total_supply": total,
        "change_24h_pct": tether_change,
        "verdict": verdict,
        "confidence": 0.5,  # Approximation only
    }
