"""
Unit tests for utils.py
"""
import pytest
from datetime import datetime, timezone

from tradingagents_crypto.dataflows.hyperliquid.utils import (
    ms_to_dt,
    dt_to_ms,
    now_ms,
    calc_time_range,
    is_valid_interval,
)


class TestMsToDt:
    """Tests for ms_to_dt()."""

    def test_positive_ms(self):
        """Test positive milliseconds."""
        ms = 1710000000000
        dt = ms_to_dt(ms)
        assert dt.year == 2024
        assert dt.month == 3
        assert dt.day == 9  # UTC: 2024-03-09 16:00:00
        assert dt.tzinfo == timezone.utc

    def test_zero_ms(self):
        """Test zero milliseconds (Unix epoch)."""
        dt = ms_to_dt(0)
        assert dt.year == 1970
        assert dt.month == 1
        assert dt.day == 1

    def test_roundtrip(self):
        """Test ms -> dt -> ms roundtrip."""
        original_ms = 1710000000000
        dt = ms_to_dt(original_ms)
        back_to_ms = dt_to_ms(dt)
        # Should be close (within 1 second for ms precision)
        assert abs(back_to_ms - original_ms) < 1000


class TestDtToMs:
    """Tests for dt_to_ms()."""

    def test_utc_datetime(self):
        """Test UTC datetime conversion."""
        dt = datetime(2024, 3, 10, tzinfo=timezone.utc)
        ms = dt_to_ms(dt)
        assert ms == 1710028800000

    def test_naive_datetime(self):
        """Test naive datetime is treated as UTC."""
        dt = datetime(2024, 3, 10)
        ms = dt_to_ms(dt)
        assert ms == 1710028800000


class TestCalcTimeRange:
    """Tests for calc_time_range()."""

    def test_1h_interval(self):
        """Test 1h interval calculates correct range."""
        end_ms = 1710000000000
        start, end = calc_time_range("1h", days=7, end_ms=end_ms)
        # 7 days of hours: 7 * 24 * 3600 * 1000 ms
        expected_duration = 7 * 24 * 3600 * 1000
        assert end == end_ms
        assert start == end_ms - expected_duration

    def test_4h_interval(self):
        """Test 4h interval calculates correct range."""
        end_ms = 1710000000000
        start, end = calc_time_range("4h", days=7, end_ms=end_ms)
        # 7 days * 6 four-hour periods * 3600 * 1000 ms
        expected_duration = 7 * 6 * 3600 * 1000
        assert end == end_ms
        assert start == end_ms - expected_duration

    def test_1d_interval(self):
        """Test 1d interval calculates correct range."""
        end_ms = 1710000000000
        start, end = calc_time_range("1d", days=30, end_ms=end_ms)
        # 30 days of ms
        expected_duration = 30 * 24 * 3600 * 1000
        assert end == end_ms
        assert start == end_ms - expected_duration

    def test_invalid_interval(self):
        """Test invalid interval raises ValueError."""
        with pytest.raises(ValueError, match="Unknown interval"):
            calc_time_range("2h", days=7)


class TestIsValidInterval:
    """Tests for is_valid_interval()."""

    @pytest.mark.parametrize("interval", ["1h", "4h", "1d"])
    def test_valid_intervals(self, interval):
        """Test all valid intervals."""
        assert is_valid_interval(interval) is True

    @pytest.mark.parametrize("interval", ["30m", "15m", "1w", "5h", "2d", "tick"])
    def test_invalid_intervals(self, interval):
        """Test invalid intervals return False."""
        assert is_valid_interval(interval) is False
