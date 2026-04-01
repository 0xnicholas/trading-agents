"""
Aggregate all technical indicators.

Computes full indicator set on OHLCV data.
"""
import logging
from typing import Any

import pandas as pd

from .calculator import (
    calc_atr,
    calc_rsi,
    calc_macd,
    calc_bollinger_bands,
    calc_ma,
    calc_volume_ma,
)

logger = logging.getLogger(__name__)


def compute_all_indicators(
    df: pd.DataFrame,
    config: dict | None = None,
) -> pd.DataFrame:
    """
    Compute all technical indicators on OHLCV data.

    Adds columns to DataFrame:
    - atr, rsi
    - macd, macd_signal, macd_hist
    - boll_upper, boll_middle, boll_lower
    - ma7, ma24, ma50, ma200
    - vol_ma7, vol_ma24

    Args:
        df: DataFrame with [timestamp, open, high, low, close, volume]
        config: Optional config dict with indicator parameters

    Returns:
        DataFrame with all indicator columns added
    """
    if config is None:
        config = {}

    result = df.copy()

    # Periods
    atr_period = config.get("atr_period", 14)
    rsi_period = config.get("rsi_period", 14)
    macd_fast = config.get("macd_fast", 12)
    macd_slow = config.get("macd_slow", 26)
    macd_signal = config.get("macd_signal", 9)
    boll_period = config.get("boll_period", 20)
    boll_std = config.get("boll_std", 2)
    vol_periods = config.get("volume_ma_periods", [7, 24])

    # Calculate indicators
    result["atr"] = calc_atr(result, period=atr_period)
    result["rsi"] = calc_rsi(result, period=rsi_period)

    # MACD
    macd_data = calc_macd(
        result,
        fast=macd_fast,
        slow=macd_slow,
        signal=macd_signal,
    )
    result["macd"] = macd_data["macd"]
    result["macd_signal"] = macd_data["signal"]
    result["macd_hist"] = macd_data["histogram"]

    # Bollinger Bands
    boll_data = calc_bollinger_bands(result, period=boll_period, std_dev=boll_std)
    result["boll_upper"] = boll_data["upper"]
    result["boll_middle"] = boll_data["middle"]
    result["boll_lower"] = boll_data["lower"]

    # Moving Averages
    ma_data = calc_ma(result, periods=[7, 24, 50, 200])
    for key, value in ma_data.items():
        result[key] = value

    # Volume MAs
    vol_data = calc_volume_ma(result, periods=vol_periods)
    for key, value in vol_data.items():
        result[key] = value

    # Fill NaN with forward fill then backfill
    result = result.ffill().bfill().fillna(0)

    return result


def get_latest_indicators(df: pd.DataFrame) -> dict[str, Any]:
    """
    Extract latest indicator values from computed DataFrame.

    Args:
        df: DataFrame with indicator columns (from compute_all_indicators)

    Returns:
        Dict with latest values for each indicator
    """
    if df.empty:
        return {}

    latest = df.iloc[-1]
    close = latest.get("close", 0)

    result = {
        "atr": float(latest.get("atr", 0)),
        "rsi": float(latest.get("rsi", 50)),
        "macd": float(latest.get("macd", 0)),
        "macd_signal": float(latest.get("macd_signal", 0)),
        "macd_hist": float(latest.get("macd_hist", 0)),
        "boll_upper": float(latest.get("boll_upper", 0)),
        "boll_middle": float(latest.get("boll_middle", 0)),
        "boll_lower": float(latest.get("boll_lower", 0)),
        "ma7": float(latest.get("ma7", 0)),
        "ma24": float(latest.get("ma24", 0)),
        "ma50": float(latest.get("ma50", 0)),
        "ma200": float(latest.get("ma200", 0)),
        "vol_ma7": float(latest.get("vol_ma7", 0)),
        "vol_ma24": float(latest.get("vol_ma24", 0)),
        # ATR as percentage of price
        "atr_pct": float(latest.get("atr", 0) / close * 100) if close > 0 else 0,
    }

    return result
