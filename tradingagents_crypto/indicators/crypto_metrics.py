"""
Crypto-specific metrics and indicators.

Funding rate, OI, orderbook imbalance, volatility position.
"""
import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def calc_funding_rate_annualized(rate: float) -> float:
    """
    Convert 8h funding rate to annualized.

    Args:
        rate: 8h funding rate (e.g., 0.0001 = 0.01%)

    Returns:
        Annualized rate (e.g., 0.1095 = 10.95%)
    """
    return rate * 3 * 365


def calc_oi_change_rate(
    oi_current: float,
    oi_24h_ago: float,
) -> float:
    """
    Calculate percentage change in open interest.

    Args:
        oi_current: Current OI value
        oi_24h_ago: OI 24 hours ago

    Returns:
        Change as percentage (e.g., 0.05 = 5% increase)
    """
    if oi_24h_ago == 0:
        return 0.0
    return (oi_current - oi_24h_ago) / oi_24h_ago


def calc_orderbook_imbalance(
    bids: list[list[float]],
    asks: list[list[float]],
) -> float:
    """
    Calculate orderbook imbalance ratio.

    Args:
        bids: [[price, size], ...] sorted by price descending
        asks: [[price, size], ...] sorted by price ascending

    Returns:
        Ratio of bid_depth / ask_depth
        > 1.0 = more bids (bullish)
        < 1.0 = more asks (bearish)
        = 1.0 = balanced
    """
    bid_depth = sum(size for _, size in bids)
    ask_depth = sum(size for _, size in asks)

    if ask_depth == 0:
        return 1.0

    return bid_depth / ask_depth


def calc_volatility_position(
    atr_pct: float,
    atr_history: list[float],
) -> dict[str, Any]:
    """
    Calculate current volatility position in historical context.

    Args:
        atr_pct: Current ATR as percentage of price
        atr_history: List of historical ATR% values

    Returns:
        Dict with:
        - position: "low" | "medium" | "high" | "extreme_high"
        - percentile: Percentile in history (0.0-1.0)
    """
    if not atr_history:
        return {"position": "unknown", "percentile": None}

    # Calculate percentile
    below_count = sum(1 for v in atr_history if v < atr_pct)
    percentile = below_count / len(atr_history)

    # Determine position
    if percentile > 0.9:
        position = "extreme_high"
    elif percentile > 0.7:
        position = "high"
    elif percentile > 0.3:
        position = "medium"
    else:
        position = "low"

    return {
        "position": position,
        "percentile": round(percentile, 3),
    }


def get_trend_direction(
    df: pd.DataFrame,
    ma_short: int = 50,
    ma_long: int = 200,
) -> str:
    """
    Determine trend direction from MA cross.

    Args:
        df: DataFrame with ma{short} and ma{long} columns
        ma_short: Short MA period
        ma_long: Long MA period

    Returns:
        "bullish" | "bearish" | "neutral"
    """
    if df.empty:
        return "neutral"

    latest = df.iloc[-1]
    ma_s = latest.get(f"ma{ma_short}", 0)
    ma_l = latest.get(f"ma{ma_long}", 0)

    if ma_s > ma_l:
        return "bullish"
    elif ma_s < ma_l:
        return "bearish"
    return "neutral"


def calc_volume_anomaly(
    volume_current: float,
    volume_ma: float,
    threshold: float = 1.5,
) -> dict[str, Any]:
    """
    Detect volume anomaly.

    Args:
        volume_current: Current volume
        volume_ma: Moving average volume
        threshold: Ratio to consider anomalous (default: 1.5)

    Returns:
        Dict with ratio and anomaly status
    """
    if volume_ma == 0:
        return {
            "ratio": 0.0,
            "is_anomaly": False,
            "label": "normal",
        }

    ratio = volume_current / volume_ma
    is_anomaly = ratio > threshold

    if ratio > 2.0:
        label = "extreme"
    elif ratio > threshold:
        label = "elevated"
    else:
        label = "normal"

    return {
        "ratio": round(ratio, 2),
        "is_anomaly": is_anomaly,
        "label": label,
    }
