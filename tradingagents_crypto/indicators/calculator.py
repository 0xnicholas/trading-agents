"""
Technical indicators for crypto trading.

Uses `ta` library for calculations.
"""
import logging
from typing import Annotated

import pandas as pd
import ta
from ta.volatility import BollingerBands, AverageTrueRange
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator, EMAIndicator, MACD as TaMACD

logger = logging.getLogger(__name__)


def calc_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range (ATR)."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    atr = AverageTrueRange(high, low, close, window=period)
    return atr.average_true_range()


def calc_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI)."""
    rsi = RSIIndicator(df["close"], window=period)
    return rsi.rsi()


def calc_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> dict[str, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    Returns dict with:
    - macd: MACD line
    - signal: Signal line
    - histogram: MACD - Signal
    """
    macd_indicator = TaMACD(
        df["close"],
        window_fast=fast,
        window_slow=slow,
        window_sign=signal,
    )
    return {
        "macd": macd_indicator.macd(),
        "signal": macd_indicator.macd_signal(),
        "histogram": macd_indicator.macd_diff(),
    }


def calc_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    std_dev: int = 2,
) -> dict[str, pd.Series]:
    """
    Calculate Bollinger Bands.

    Returns dict with:
    - upper: Upper band
    - middle: Middle band (SMA)
    - lower: Lower band
    """
    boll = BollingerBands(df["close"], window=period, window_dev=std_dev)
    return {
        "upper": boll.bollinger_hband(),
        "middle": boll.bollinger_mavg(),
        "lower": boll.bollinger_lband(),
    }


def calc_ma(
    df: pd.DataFrame,
    periods: list[int] | None = None,
) -> dict[str, pd.Series]:
    """
    Calculate Simple Moving Averages.

    Args:
        df: DataFrame with 'close' column
        periods: List of periods (default: [7, 24, 50, 200])

    Returns:
        Dict mapping "ma{period}" -> Series
    """
    if periods is None:
        periods = [7, 24, 50, 200]

    result = {}
    for p in periods:
        sma = SMAIndicator(df["close"], window=p)
        result[f"ma{p}"] = sma.sma_indicator()

    return result


def calc_ema(
    df: pd.DataFrame,
    periods: list[int] | None = None,
) -> dict[str, pd.Series]:
    """Calculate Exponential Moving Averages."""
    if periods is None:
        periods = [12, 26, 50, 200]

    result = {}
    for p in periods:
        ema = EMAIndicator(df["close"], window=p)
        result[f"ema{p}"] = ema.ema_indicator()

    return result


def calc_volume_ma(
    df: pd.DataFrame,
    periods: list[int] | None = None,
) -> dict[str, pd.Series]:
    """Calculate Volume Moving Averages."""
    if periods is None:
        periods = [7, 24]

    result = {}
    for p in periods:
        sma = SMAIndicator(df["volume"], window=p)
        result[f"vol_ma{p}"] = sma.sma_indicator()

    return result
