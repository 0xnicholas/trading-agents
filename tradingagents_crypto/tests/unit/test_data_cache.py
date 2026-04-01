"""
Unit tests for BacktestDataCache.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil

from tradingagents_crypto.backtest.data_cache import (
    BacktestDataCache,
    GapCheckResult,
    DataGap,
)


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory."""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)


@pytest.fixture
def sample_candles():
    """Generate sample candle data."""
    np.random.seed(42)
    n = 100
    timestamps = pd.date_range(start="2024-01-01", periods=n, freq="h")
    prices = 50000 * np.exp(np.cumsum(np.random.normal(0, 0.001, n)))

    return pd.DataFrame({
        "timestamp": timestamps,
        "open": prices * 0.99,
        "high": prices * 1.01,
        "low": prices * 0.98,
        "close": prices,
        "volume": np.random.uniform(1000, 5000, n),
    })


@pytest.fixture
def sample_funding():
    """Generate sample funding data."""
    n = 50
    timestamps = pd.date_range(start="2024-01-01", periods=n, freq="8h")

    return pd.DataFrame({
        "timestamp": timestamps,
        "funding_rate": np.random.uniform(-0.0001, 0.0001, n),
    })


class TestBacktestDataCache:
    """Tests for BacktestDataCache."""

    def test_save_and_load_candles(self, temp_cache_dir, sample_candles):
        """T_CACHE_01: Save and load candles."""
        cache = BacktestDataCache(cache_dir=temp_cache_dir)

        # Save with end date exclusive semantics (end=2024-01-05 means through Jan 4)
        path = cache.save_candles(sample_candles, "BTC", "1h", "2024-01-01", "2024-01-05")
        assert path.exists()

        # Load with end=2024-01-06 to include all Jan 5 candles (exclusive semantics)
        loaded = cache.load_candles("BTC", "1h", "2024-01-01", "2024-01-06")
        assert loaded is not None
        assert len(loaded) == len(sample_candles)

    def test_load_nonexistent_returns_none(self, temp_cache_dir):
        """T_CACHE_02: Load non-existent file returns None."""
        cache = BacktestDataCache(cache_dir=temp_cache_dir)
        result = cache.load_candles("NONEXISTENT", "1h")
        assert result is None

    def test_get_candles_with_loader(self, temp_cache_dir, sample_candles):
        """T_CACHE_03: Get candles uses loader if not cached."""
        cache = BacktestDataCache(cache_dir=temp_cache_dir)

        loader_called = False

        def mock_loader(symbol, interval, start, end):
            nonlocal loader_called
            loader_called = True
            return sample_candles.head(10)

        # First call should use loader
        result = cache.get_candles("BTC", "1h", "2024-01-01", "2024-01-05", mock_loader)
        assert loader_called
        assert len(result) == 10

    def test_filter_by_date(self, temp_cache_dir, sample_candles):
        """T_CACHE_04: Date filtering works."""
        cache = BacktestDataCache(cache_dir=temp_cache_dir)
        cache.save_candles(sample_candles, "BTC", "1h")

        # Filter to first day
        filtered = cache.load_candles("BTC", "1h", "2024-01-01", "2024-01-02")
        assert filtered is not None
        assert len(filtered) <= 24  # ~24 hours in a day

    def test_save_and_load_funding(self, temp_cache_dir, sample_funding):
        """T_CACHE_05: Save and load funding history."""
        cache = BacktestDataCache(cache_dir=temp_cache_dir)

        path = cache.save_funding_history(sample_funding, "ETH", "2024-01-01", "2024-01-05")
        assert path.exists()

        loaded = cache.load_funding_history("ETH")
        assert loaded is not None
        assert len(loaded) == len(sample_funding)


class TestCheckGaps:
    """Tests for gap detection."""

    def test_no_gaps(self, sample_candles):
        """No gaps in continuous data."""
        cache = BacktestDataCache()
        result = cache.check_gaps(sample_candles, interval_hours=1)

        assert result.total_gaps == 0
        assert result.total_missing_bars == 0
        assert result.completeness == 1.0

    def test_gap_detection(self):
        """T_CACHE_06: Detect gaps in data."""
        cache = BacktestDataCache()

        # Create data with a gap
        df = pd.DataFrame({
            "timestamp": pd.to_datetime([
                "2024-01-01 00:00",
                "2024-01-01 01:00",
                "2024-01-01 02:00",
                "2024-01-01 10:00",  # Gap: missing 03:00-09:00
                "2024-01-01 11:00",
            ]),
            "close": [100, 101, 102, 103, 104],
        })

        result = cache.check_gaps(df, interval_hours=1)

        assert result.total_gaps == 1
        assert result.total_missing_bars == 7  # 7 missing hours
        assert result.completeness < 1.0

    def test_empty_dataframe(self):
        """Empty DataFrame handled gracefully."""
        cache = BacktestDataCache()
        result = cache.check_gaps(pd.DataFrame())

        assert result.total_gaps == 0
        assert result.completeness == 0.0

    def test_none_dataframe(self):
        """None DataFrame handled gracefully."""
        cache = BacktestDataCache()
        result = cache.check_gaps(None)

        assert result.total_gaps == 0
        assert result.completeness == 0.0


class TestMergeCandles:
    """Tests for merging candles."""

    def test_merge_no_overlap(self, sample_candles):
        """Merge two non-overlapping datasets."""
        cache = BacktestDataCache()

        first = sample_candles.head(50)
        second = sample_candles.tail(50)

        merged = cache.merge_candles(first, second)

        assert len(merged) == 100
        assert len(merged) == len(first) + len(second)

    def test_merge_with_overlap(self, sample_candles):
        """Merge with overlapping timestamps."""
        cache = BacktestDataCache()

        first = sample_candles.head(50)
        second = sample_candles.iloc[40:90]  # Overlapping

        merged = cache.merge_candles(first, second)

        # Should keep last value for duplicates
        assert len(merged) <= len(first) + len(second)
        assert not merged.duplicated(subset=["timestamp"]).any()

    def test_merge_empty_first(self, sample_candles):
        """Merge with empty first DataFrame."""
        cache = BacktestDataCache()
        merged = cache.merge_candles(pd.DataFrame(), sample_candles)
        assert len(merged) == len(sample_candles)

    def test_merge_empty_second(self, sample_candles):
        """Merge with empty second DataFrame."""
        cache = BacktestDataCache()
        merged = cache.merge_candles(sample_candles, pd.DataFrame())
        assert len(merged) == len(sample_candles)


class TestClearCache:
    """Tests for cache clearing."""

    def test_clear_all(self, temp_cache_dir, sample_candles):
        """Clear all cached files."""
        cache = BacktestDataCache(cache_dir=temp_cache_dir)
        cache.save_candles(sample_candles, "BTC", "1h")
        cache.save_candles(sample_candles, "ETH", "1h")

        count = cache.clear_cache()

        assert count == 2
        assert len(list(temp_cache_dir.glob("*.parquet"))) == 0

    def test_clear_by_symbol(self, temp_cache_dir, sample_candles):
        """Clear only specific symbol."""
        cache = BacktestDataCache(cache_dir=temp_cache_dir)
        cache.save_candles(sample_candles, "BTC", "1h")
        cache.save_candles(sample_candles, "ETH", "1h")

        count = cache.clear_cache(symbol="BTC")

        assert count == 1
        assert len(list(temp_cache_dir.glob("*BTC*"))) == 0
        assert len(list(temp_cache_dir.glob("*ETH*"))) == 1
