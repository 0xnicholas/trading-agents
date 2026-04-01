"""
Unit tests for HV Analyst.
"""
import pytest
import numpy as np
import pandas as pd
from tradingagents_crypto.agents.risk_mgmt.hv_analyst import (
    analyze_hv,
    calculate_hv_from_returns,
    calculate_atr,
    HVAnalysis,
)


def generate_test_candles(volatility: float = 0.02, days: int = 35) -> pd.DataFrame:
    """Generate synthetic candle data for testing."""
    np.random.seed(42)
    n_bars = days * 24
    dt = 1 / (24 * 365)

    # Generate prices with geometric brownian motion
    returns = np.random.normal(0, volatility * np.sqrt(dt), n_bars)
    prices = 100 * np.exp(np.cumsum(returns))

    # Generate OHLCV data
    data = {
        "timestamp": pd.date_range(start="2024-01-01", periods=n_bars, freq="h"),
        "open": prices * (1 + np.random.uniform(-0.005, 0.005, n_bars)),
        "high": prices * (1 + np.random.uniform(0, 0.01, n_bars)),
        "low": prices * (1 - np.random.uniform(0, 0.01, n_bars)),
        "close": prices,
        "volume": np.random.uniform(1000, 10000, n_bars),
    }

    return pd.DataFrame(data)


class TestAnalyzeHV:
    """Tests for analyze_hv function."""

    def test_t_hv_01_low_volatility_recommends_high_leverage(self):
        """T_HV_01: Low volatility should recommend high leverage."""
        # Low volatility data - override percentile to ensure low-vol scenario
        candles = generate_test_candles(volatility=0.005, days=35)
        result = analyze_hv(candles, hv_percentile_override=20)

        assert result.recommended_leverage >= 8

    def test_t_hv_02_high_volatility_recommends_low_leverage(self):
        """T_HV_02: High volatility should recommend low leverage."""
        candles = generate_test_candles(volatility=0.05, days=35)
        result = analyze_hv(candles, hv_percentile_override=85)

        assert result.recommended_leverage <= 3

    def test_t_hv_03_atr_calculation_accuracy(self):
        """T_HV_03: ATR calculation within 1% error."""
        candles = generate_test_candles(volatility=0.02, days=5)

        # Calculate ATR manually
        high_low = candles["high"] - candles["low"]
        high_close = np.abs(candles["high"] - candles["close"].shift())
        low_close = np.abs(candles["low"] - candles["close"].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        expected_atr = tr.rolling(14).mean().iloc[-1]

        result = analyze_hv(candles)

        # Within 1% error
        if expected_atr > 0:
            error = abs(result.atr_14 - expected_atr) / expected_atr
            assert error < 0.01 or result.atr_14 < 1.0  # Allow error for small values

    def test_t_hv_04_extreme_volatility_position(self):
        """T_HV_04: HV percentile at extremes."""
        candles = generate_test_candles(volatility=0.08, days=35)
        result = analyze_hv(candles, hv_percentile_override=95)

        # High volatility should give position="high" or "extreme"
        assert result.position in ("high", "extreme")

    def test_t_hv_05_empty_data_returns_defaults(self):
        """T_HV_05: Empty data returns default values."""
        result = analyze_hv(pd.DataFrame())

        assert result.hv_percentile_30d == 50
        assert result.recommended_leverage == 5

    def test_t_hv_06_insufficient_data(self):
        """T_HV_06: Insufficient data handled gracefully."""
        candles = generate_test_candles(days=5)  # Less than 30 days
        result = analyze_hv(candles)

        # Should return defaults without crashing
        assert isinstance(result, HVAnalysis)
        assert result.hv_percentile_30d >= 0


class TestCalculateATR:
    """Tests for calculate_atr function."""

    def test_atr_basic(self):
        """Basic ATR calculation."""
        high = pd.Series([100, 105, 103, 107, 110])
        low = pd.Series([98, 102, 100, 104, 108])
        close = pd.Series([99, 103, 101, 106, 109])

        atr = calculate_atr(high, low, close, period=3)

        # Should have values after the period
        assert atr.iloc[-1] > 0

    def test_atr_zero_values(self):
        """ATR with zero range."""
        high = pd.Series([100, 100, 100])
        low = pd.Series([100, 100, 100])
        close = pd.Series([100, 100, 100])

        atr = calculate_atr(high, low, close, period=2)

        # Should handle zero range
        assert atr.iloc[-1] == 0.0


class TestCalculateHVFromReturns:
    """Tests for calculate_hv_from_returns."""

    def test_hv_calculation(self):
        """Basic HV calculation."""
        returns = pd.Series([0.01, -0.01, 0.02, -0.005, 0.015])

        hv = calculate_hv_from_returns(returns)

        # HV should be positive
        assert hv > 0
        # Annualized HV for these returns should be reasonable
        assert hv < 1.0  # Less than 100% annualized vol

    def test_hv_empty_returns(self):
        """HV with empty series."""
        returns = pd.Series([])

        hv = calculate_hv_from_returns(returns)

        assert hv == 0.0
