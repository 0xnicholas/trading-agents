"""
Cross-chain correlation data.

Calculates 7-day Pearson correlation between BTC/ETH/SOL prices.
"""
import logging
from datetime import datetime, timezone, timedelta

from tradingagents_crypto.dataflows.coincap import CoinCapClient

logger = logging.getLogger(__name__)


def get_price_history_7d(
    asset_id: str,
    cache=None,
) -> list[dict]:
    """
    Get 7-day price history for an asset.

    Note: CoinCap doesn't provide historical OHLCV in free tier.
    This is a placeholder - implement when API is accessible.

    Args:
        asset_id: CoinCap asset ID (e.g., "bitcoin", "ethereum", "solana")
        cache: CacheManager instance

    Returns:
        List of dicts with timestamp and price
    """
    # TODO: Implement when CoinCap historical API is accessible
    return []


def calc_pearson_correlation(x: list[float], y: list[float]) -> float:
    """
    Calculate Pearson correlation coefficient.

    Args:
        x: First series of values
        y: Second series of values

    Returns:
        Correlation coefficient (-1 to 1)
    """
    if len(x) != len(y) or len(x) < 2:
        return 0.0

    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n

    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denom_x = sum((x[i] - mean_x) ** 2 for i in range(n)) ** 0.5
    denom_y = sum((y[i] - mean_y) ** 2 for i in range(n)) ** 0.5

    if denom_x == 0 or denom_y == 0:
        return 0.0

    return numerator / (denom_x * denom_y)


def get_correlations(cache=None) -> dict:
    """
    Get cross-chain correlations between BTC, ETH, SOL.

    Note: Placeholder - requires historical price data.

    Returns:
        Dict with:
        - btc_eth_corr_7d: float
        - btc_sol_corr_7d: float
        - verdict: str
        - confidence: float
    """
    # TODO: Implement with real historical data
    return {
        "btc_eth_corr_7d": 0.0,  # Placeholder
        "btc_sol_corr_7d": 0.0,  # Placeholder
        "verdict": "Historical correlation data not available",
        "confidence": 0.3,  # Low - placeholder
        "note": "CoinCap free tier doesn't provide historical OHLCV",
    }


def interpret_correlation(btc_eth: float, btc_sol: float) -> dict:
    """
    Interpret correlation values for trading.

    Args:
        btc_eth: BTC/ETH correlation
        btc_sol: BTC/SOL correlation

    Returns:
        Dict with interpretation
    """
    # High correlation (>0.7) = market moves together
    # Low correlation (<0.5) = market diverging

    if btc_eth > 0.7 and btc_sol > 0.7:
        regime = "risk_on"
        verdict = "High correlation - market moves together"
    elif btc_eth < 0.5 and btc_sol < 0.5:
        regime = "分化"
        verdict = "Low correlation - market diverging"
    elif btc_sol < btc_eth - 0.2:
        regime = "altcoin_rotation"
        verdict = "SOL decoupling from BTC - potential alt season"
    else:
        regime = "neutral"
        verdict = "Moderate correlation"
        btc_eth = 0.0
        btc_sol = 0.0

    return {
        "regime": regime,
        "verdict": verdict,
        "confidence": 0.8,
    }
