"""
Historical Volatility (HV) Analyst.

Calculates historical volatility, HV percentile, and ATR for risk management.
"""
import logging
from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Leverage recommendation thresholds (based on HV percentile)
LEVERAGE_LOW_THRESHOLD = 30      # < 30% → low volatility → 8-10x
LEVERAGE_MEDIUM_THRESHOLD = 70  # 30-70% → normal → 5-7x
LEVERAGE_HIGH_THRESHOLD = 90     # 70-90% → high → 3-4x
# > 90% → extreme → 1-2x

# Position risk labels
POSITION_LOW = "low"
POSITION_MEDIUM = "medium"
POSITION_HIGH = "high"
POSITION_EXTREME = "extreme"


@dataclass
class HVAnalysis:
    """Historical volatility analysis result."""
    hv_annualized: float      # 30-day annualized volatility
    hv_percentile_30d: int    # HV percentile over past 30 days (0-100)
    atr_14: float             # ATR with 14 periods
    atr_pct: float            # ATR as percentage of price
    position: Literal["low", "medium", "high", "extreme"]
    recommended_leverage: int  # Recommended leverage based on volatility
    verdict: str               # Trading recommendation


def analyze_hv(candles_1h: pd.DataFrame, hv_percentile_override: Optional[int] = None) -> HVAnalysis:
    """
    Calculate historical volatility and ATR from 1h candle data.

    Args:
        candles_1h: DataFrame with columns [timestamp, open, high, low, close, volume]

    Returns:
        HVAnalysis with volatility metrics and recommendations
    """
    if candles_1h is None or len(candles_1h) < 30:
        logger.warning("Insufficient data for HV analysis, returning defaults")
        return _default_hv_analysis()

    # Use last 30 days (~720 hours) for HV calculation
    hv_window = candles_1h.tail(30 * 24).copy()

    # Calculate returns
    returns = hv_window["close"].pct_change().dropna()

    if len(returns) < 10:
        return _default_hv_analysis()

    # Calculate annualized HV
    hv_annualized = returns.std() * np.sqrt(365)

    # Calculate HV percentile (where current HV sits in recent history)
    # Use rolling 30-period HV to get distribution
    if len(returns) >= 30:
        rolling_hv = returns.rolling(30).std() * np.sqrt(365)
        current_hv = rolling_hv.iloc[-1]
        # Percentile: what % of historical values are below current
        hv_percentile = int((rolling_hv < current_hv).mean() * 100)
    else:
        hv_percentile = 50  # Default to median

    # Override percentile if provided (for testing)
    if hv_percentile_override is not None:
        hv_percentile = hv_percentile_override

    # Calculate ATR (14 periods)
    high_low = hv_window["high"] - hv_window["low"]
    high_close = np.abs(hv_window["high"] - hv_window["close"].shift())
    low_close = np.abs(hv_window["low"] - hv_window["close"].shift())

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr_14 = tr.rolling(14).mean().iloc[-1]

    # ATR as percentage of current price
    current_price = hv_window["close"].iloc[-1]
    atr_pct = atr_14 / current_price if current_price > 0 else 0

    # Determine position and recommended leverage
    if hv_percentile < LEVERAGE_LOW_THRESHOLD:
        position = POSITION_LOW
        recommended_leverage = 9  # 8-10x
        verdict = "低波动环境，可适当增加仓位"
    elif hv_percentile < LEVERAGE_MEDIUM_THRESHOLD:
        position = POSITION_MEDIUM
        recommended_leverage = 6  # 5-7x
        verdict = "正常波动环境，仓位适中"
    elif hv_percentile < LEVERAGE_HIGH_THRESHOLD:
        position = POSITION_HIGH
        recommended_leverage = 3  # 3-4x
        verdict = "高波动环境，建议降低仓位"
    else:
        position = POSITION_EXTREME
        recommended_leverage = 1  # 1-2x
        verdict = "极端波动，建议观望或极小仓位"

    return HVAnalysis(
        hv_annualized=round(hv_annualized, 6),
        hv_percentile_30d=hv_percentile,
        atr_14=round(atr_14, 4),
        atr_pct=round(atr_pct, 6),
        position=position,
        recommended_leverage=recommended_leverage,
        verdict=verdict,
    )


def _default_hv_analysis() -> HVAnalysis:
    """Return default HV analysis when data is insufficient."""
    return HVAnalysis(
        hv_annualized=0.0,
        hv_percentile_30d=50,
        atr_14=0.0,
        atr_pct=0.0,
        position=POSITION_MEDIUM,
        recommended_leverage=5,
        verdict="数据不足，使用默认建议",
    )


def calculate_hv_from_returns(returns: pd.Series) -> float:
    """
    Calculate annualized HV from a series of returns.

    Args:
        returns: Series of returns (e.g., hourly returns)

    Returns:
        Annualized volatility
    """
    if len(returns) < 2:
        return 0.0
    return returns.std() * np.sqrt(365)


def calculate_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """
    Calculate Average True Range (ATR).

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: ATR period (default 14)

    Returns:
        Series of ATR values
    """
    high_low = high - low
    high_close = np.abs(high - close.shift())
    low_close = np.abs(low - close.shift())

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()

    return atr
