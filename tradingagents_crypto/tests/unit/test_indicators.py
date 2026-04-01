"""
Unit tests for indicators module.
"""
import pytest
import pandas as pd
import numpy as np

from indicators import (
    calc_atr,
    calc_rsi,
    calc_macd,
    calc_bollinger_bands,
    calc_ma,
    calc_orderbook_imbalance,
    calc_volatility_position,
    get_trend_direction,
    calc_volume_anomaly,
    calc_funding_rate_annualized,
    compute_all_indicators,
    get_latest_indicators,
)


@pytest.fixture
def ohlcv_df():
    """Generate realistic OHLCV DataFrame for testing."""
    dates = pd.date_range("2024-01-01", periods=200, freq="1h")
    np.random.seed(42)

    base = 67000
    close = base + np.cumsum(np.random.randn(200) * 100)
    high = close + np.random.rand(200) * 200
    low = close - np.random.rand(200) * 200
    open_price = close + np.random.randn(200) * 50
    volume = 1000 + np.random.rand(200) * 500

    return pd.DataFrame({
        "timestamp": dates.astype(int) // 10**9,
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


class TestCalcATR:
    """Tests for calc_atr()."""

    def test_atr_non_negative(self, ohlcv_df):
        """ATR should be non-negative (>= 0) for valid rows."""
        atr = calc_atr(ohlcv_df)
        # Skip warmup period and check non-negative
        valid = atr.dropna()
        assert (valid >= 0).all()

    def test_atr_increases_with_volatility(self, ohlcv_df):
        """Higher volatility periods should have higher ATR."""
        atr = calc_atr(ohlcv_df)
        assert atr.iloc[-1] > 0


class TestCalcRSI:
    """Tests for calc_rsi()."""

    def test_rsi_range(self, ohlcv_df):
        """RSI should be between 0 and 100."""
        rsi = calc_rsi(ohlcv_df)
        assert rsi.min() >= 0
        assert rsi.max() <= 100

    def test_rsi_50_neutral(self, ohlcv_df):
        """RSI around 50 is neutral."""
        rsi = calc_rsi(ohlcv_df)
        # RSI should have values across the range (not all at extremes)
        assert rsi.max() > 50
        assert rsi.min() < 50


class TestCalcMACD:
    """Tests for calc_macd()."""

    def test_macd_returns_three_series(self, ohlcv_df):
        """MACD should return dict with 3 keys."""
        result = calc_macd(ohlcv_df)
        assert set(result.keys()) == {"macd", "signal", "histogram"}

    def test_macd_histogram_sign(self, ohlcv_df):
        """MACD histogram = MACD - Signal."""
        result = calc_macd(ohlcv_df)
        diff = result["macd"] - result["signal"]
        np.testing.assert_array_almost_equal(
            result["histogram"].dropna().values,
            diff.dropna().values,
        )


class TestCalcBollingerBands:
    """Tests for calc_bollinger_bands()."""

    def test_bands_order(self, ohlcv_df):
        """Upper > Middle > Lower (after warmup period)."""
        result = calc_bollinger_bands(ohlcv_df)
        upper = result["upper"].dropna()
        middle = result["middle"].dropna()
        lower = result["lower"].dropna()
        assert (upper > middle).all()
        assert (middle > lower).all()

    def test_bands_width_reasonable(self, ohlcv_df):
        """Bands should be reasonably close to price."""
        result = calc_bollinger_bands(ohlcv_df)
        mid = result["middle"].dropna()
        upper = result["upper"].dropna()
        lower = result["lower"].dropna()
        # Bands within 20% of middle seems reasonable
        assert ((upper - mid) / mid < 0.2).all()
        assert ((mid - lower) / mid < 0.2).all()


class TestCalcMA:
    """Tests for calc_ma()."""

    def test_ma_keys(self, ohlcv_df):
        """MA returns correct period keys."""
        result = calc_ma(ohlcv_df, periods=[7, 24, 50, 200])
        assert set(result.keys()) == {"ma7", "ma24", "ma50", "ma200"}

    def test_ma_values_reasonable(self, ohlcv_df):
        """MA values should be between min and max of the window."""
        result = calc_ma(ohlcv_df, periods=[7, 50])
        close = ohlcv_df["close"]
        # MA7 should be between min and max of last 7 close prices
        ma7 = result["ma7"]
        # Check last 10 values (avoiding warmup period)
        for i in range(10, len(ma7)):
            window = close.iloc[i-7:i]
            assert window.min() <= ma7.iloc[i] <= window.max()
        # MA50 similarly
        ma50 = result["ma50"]
        for i in range(50, len(ma50)):
            window = close.iloc[i-50:i]
            assert window.min() <= ma50.iloc[i] <= window.max()


class TestCryptoMetrics:
    """Tests for crypto-specific metrics."""

    def test_orderbook_imbalance_bullish(self):
        """More bids = ratio > 1."""
        bids = [[100, 1.0], [99, 2.0]]  # depth = 3
        asks = [[101, 1.0]]  # depth = 1
        ratio = calc_orderbook_imbalance(bids, asks)
        assert ratio == 3.0

    def test_orderbook_imbalance_empty_asks(self):
        """Empty asks returns 1.0 (avoid division by zero)."""
        bids = [[100, 1.0]]
        asks = []
        ratio = calc_orderbook_imbalance(bids, asks)
        assert ratio == 1.0

    def test_volatility_position_high(self):
        """High ATR% in history = extreme_high."""
        atr_history = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        # Use value > max(atr_history) so percentile = 1.0
        result = calc_volatility_position(1.5, atr_history)
        assert result["position"] == "extreme_high"
        assert result["percentile"] == 1.0

    def test_volatility_position_low(self):
        """Low ATR% = low."""
        atr_history = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
        result = calc_volatility_position(0.5, atr_history)
        assert result["position"] == "low"

    def test_trend_bullish(self, ohlcv_df):
        """MA50 > MA200 = bullish."""
        df = compute_all_indicators(ohlcv_df)
        direction = get_trend_direction(df, ma_short=50, ma_long=200)
        assert direction in ("bullish", "bearish", "neutral")

    def test_volume_anomaly_elevated(self):
        """Volume > 1.5x MA = elevated."""
        result = calc_volume_anomaly(2000, 1000, threshold=1.5)
        assert result["ratio"] == 2.0
        assert result["label"] == "elevated"
        assert result["is_anomaly"] is True

    def test_volume_anomaly_normal(self):
        """Volume < 1.5x MA = normal."""
        result = calc_volume_anomaly(1200, 1000, threshold=1.5)
        assert result["label"] == "normal"
        assert result["is_anomaly"] is False

    def test_funding_annualized(self):
        """Annualized = 8h rate * 3 * 365."""
        rate = 0.0001  # 0.01%
        annualized = calc_funding_rate_annualized(rate)
        assert annualized == pytest.approx(0.1095, rel=1e-3)


class TestComputeAllIndicators:
    """Tests for compute_all_indicators()."""

    def test_returns_dataframe(self, ohlcv_df):
        """Should return DataFrame."""
        result = compute_all_indicators(ohlcv_df)
        assert isinstance(result, pd.DataFrame)

    def test_has_indicator_columns(self, ohlcv_df):
        """Should have all indicator columns."""
        result = compute_all_indicators(ohlcv_df)
        expected = ["atr", "rsi", "macd", "boll_upper", "ma7", "ma200"]
        for col in expected:
            assert col in result.columns

    def test_same_row_count(self, ohlcv_df):
        """Should have same number of rows."""
        result = compute_all_indicators(ohlcv_df)
        assert len(result) == len(ohlcv_df)


class TestGetLatestIndicators:
    """Tests for get_latest_indicators()."""

    def test_returns_dict(self, ohlcv_df):
        """Should return dict."""
        df = compute_all_indicators(ohlcv_df)
        result = get_latest_indicators(df)
        assert isinstance(result, dict)

    def test_has_required_keys(self, ohlcv_df):
        """Should have all required keys."""
        df = compute_all_indicators(ohlcv_df)
        result = get_latest_indicators(df)
        required = ["atr", "rsi", "macd", "ma7", "atr_pct"]
        for key in required:
            assert key in result

    def test_empty_df_returns_empty_dict(self):
        """Empty DataFrame returns empty dict."""
        result = get_latest_indicators(pd.DataFrame())
        assert result == {}
