"""
Unit tests for Prometheus metrics.
"""
import pytest
from prometheus_client import REGISTRY
from tradingagents_crypto.utils.metrics import (
    orders_total,
    pnl_gauge,
    cache_hits,
    cache_hit_ratio,
    position_size,
    win_rate,
    agent_response_time,
)


class TestMetrics:
    """Tests for Prometheus metrics."""

    def test_orders_total_increments(self):
        """Test that orders_total counter increments."""
        initial = orders_total.labels(
            symbol="BTC", side="long", result="filled"
        )._value.get()
        orders_total.labels(symbol="BTC", side="long", result="filled").inc()
        after = orders_total.labels(
            symbol="BTC", side="long", result="filled"
        )._value.get()
        assert after == initial + 1

    def test_orders_total_with_labels(self):
        """Test orders_total with different label combinations."""
        orders_total.labels(symbol="ETH", side="short", result="rejected").inc(2)
        value = orders_total.labels(
            symbol="ETH", side="short", result="rejected"
        )._value.get()
        assert value >= 2

    def test_pnl_gauge_sets(self):
        """Test that pnl_gauge can be set."""
        pnl_gauge.labels(symbol="BTC").set(1234.56)
        assert pnl_gauge.labels(symbol="BTC")._value.get() == 1234.56

    def test_pnl_gauge_updates(self):
        """Test that pnl_gauge updates correctly."""
        pnl_gauge.labels(symbol="ETH").set(1000.0)
        pnl_gauge.labels(symbol="ETH").set(2000.0)
        assert pnl_gauge.labels(symbol="ETH")._value.get() == 2000.0

    def test_position_size_gauge(self):
        """Test position_size gauge."""
        position_size.labels(symbol="BTC").set(5000.0)
        assert position_size.labels(symbol="BTC")._value.get() == 5000.0

    def test_win_rate_gauge(self):
        """Test win_rate gauge (0-1 range)."""
        win_rate.labels(symbol="BTC").set(0.75)
        assert win_rate.labels(symbol="BTC")._value.get() == 0.75

    def test_cache_hit_increments(self):
        """Test cache_hits counter increments."""
        initial = cache_hits.labels(cache="prices", result="hit")._value.get()
        cache_hits.labels(cache="prices", result="hit").inc()
        after = cache_hits.labels(cache="prices", result="hit")._value.get()
        assert after == initial + 1

    def test_cache_hit_ratio_calculation(self):
        """Test cache hit ratio calculation using separate cache name."""
        # Use a unique cache name to avoid interference from other tests
        test_cache_name = "test_prices"
        cache_hits.labels(cache=test_cache_name, result="hit").inc(80)
        cache_hits.labels(cache=test_cache_name, result="miss").inc(20)

        # Calculate ratio manually
        hit = cache_hits.labels(cache=test_cache_name, result="hit")._value.get()
        miss = cache_hits.labels(cache=test_cache_name, result="miss")._value.get()
        ratio = hit / (hit + miss)
        assert abs(ratio - 0.8) < 0.01

    def test_cache_hit_ratio_gauge(self):
        """Test cache_hit_ratio gauge can be set."""
        cache_hit_ratio.labels(cache="prices").set(0.85)
        assert cache_hit_ratio.labels(cache="prices")._value.get() == 0.85

    def test_agent_response_time_histogram(self):
        """Test agent_response_time histogram records values."""
        agent_response_time.labels(agent="btc_analyst", operation="analyze").observe(1.5)
        # Histogram buckets track counts - just verify it doesn't raise
        agent_response_time.labels(agent="btc_analyst", operation="analyze").observe(0.5)

    def test_multiple_symbols_independent(self):
        """Test that different symbols have independent metrics."""
        pnl_gauge.labels(symbol="BTC").set(1000.0)
        pnl_gauge.labels(symbol="ETH").set(2000.0)

        assert pnl_gauge.labels(symbol="BTC")._value.get() == 1000.0
        assert pnl_gauge.labels(symbol="ETH")._value.get() == 2000.0

    def test_orders_with_different_results(self):
        """Test tracking different order results separately."""
        orders_total.labels(symbol="BTC", side="long", result="filled").inc()
        orders_total.labels(symbol="BTC", side="long", result="cancelled").inc()

        filled = orders_total.labels(symbol="BTC", side="long", result="filled")._value.get()
        cancelled = orders_total.labels(
            symbol="BTC", side="long", result="cancelled"
        )._value.get()

        assert filled >= 1
        assert cancelled >= 1
        # Rejected should be 0 (or default)
        rejected = orders_total.labels(
            symbol="BTC", side="long", result="rejected"
        )._value.get()
        assert rejected == 0
