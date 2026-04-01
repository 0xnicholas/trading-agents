"""
BTC Dominance data.

Data source: CoinCap.io
"""
import logging

from tradingagents_crypto.dataflows.coincap import CoinCapClient

logger = logging.getLogger(__name__)

DEFAULT_TTL = 600  # 10 minutes - BTC dominance changes slowly


def get_btc_dominance(cache=None) -> dict:
    """
    Get BTC dominance from CoinCap.

    Returns:
        Dict with:
        - btc_dominance: float (percentage, e.g., 52.3)
        - confidence: float (0.75)
    """
    client = CoinCapClient(cache=cache)
    dominance = client.get_btc_dominance()

    return {
        "btc_dominance": dominance,
        "confidence": 0.75,  # CoinCap free API
    }


def get_btc_dominance_trend(
    current: float,
    history_7d: list[float],
) -> dict:
    """
    Calculate BTC dominance trend over 7 days.

    Args:
        current: Current BTC dominance
        history_7d: List of 7 historical dominance values

    Returns:
        Dict with:
        - current: float
        - trend: str ("rising", "falling", "stable")
        - change_pct: float
        - verdict: str
    """
    if not history_7d:
        return {
            "current": current,
            "trend": "stable",
            "change_pct": 0.0,
            "verdict": "Insufficient data for trend",
            "confidence": 0.5,
        }

    # Calculate average
    avg = sum(history_7d) / len(history_7d)

    # Calculate change
    if avg > 0:
        change_pct = ((current - avg) / avg) * 100
    else:
        change_pct = 0.0

    # Determine trend
    if change_pct > 2.0:  # >2% increase
        trend = "rising"
        verdict = "BTC gaining market share"
    elif change_pct < -2.0:  # >2% decrease
        trend = "falling"
        verdict = "BTC losing market share to altcoins"
    else:
        trend = "stable"
        verdict = "BTC dominance stable"
        change_pct = 0.0  # Normalize to 0 for stable

    return {
        "current": current,
        "trend": trend,
        "change_pct": round(change_pct, 2),
        "verdict": verdict,
        "confidence": 0.75,
    }
