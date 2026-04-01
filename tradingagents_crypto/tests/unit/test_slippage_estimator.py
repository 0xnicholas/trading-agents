"""
Unit tests for Slippage Estimator.
"""
import pytest
from tradingagents_crypto.backtest.slippage_estimator import (
    estimate_slippage,
    estimate_slippage_simple,
    depth_required_for_target_slippage,
    calculate_execution_price,
    SLIPPAGE_MAX_BPS,
)


class TestEstimateSlippage:
    """Tests for estimate_slippage function."""

    def test_t_slip_01_low_slippage_ratio(self):
        """T_SLIP_01: Small position relative to depth."""
        # ratio = 1000 / 100000 = 0.01
        # slippage = min(0.01^0.7 * 10, 50) = min(0.25, 50) = 0.25 bps
        slippage = estimate_slippage(
            position_size_usd=1000,
            bid_depth_usd=100000,
            ask_depth_usd=100000,
            side="long",
        )

        assert slippage < 1  # Very low

    def test_t_slip_02_nonlinearity(self):
        """T_SLIP_02: Verify non-linear formula behavior."""
        # Doubling position shouldn't double slippage (non-linear)
        small = estimate_slippage(1000, 100000, 100000, "long")
        large = estimate_slippage(2000, 100000, 100000, "long")

        # ratio goes from 0.01 to 0.02
        # 0.01^0.7 = 0.025, 0.02^0.7 = 0.038
        # ratio of slips ≈ 0.038/0.025 = 1.52x (not 2x)
        ratio = large / small
        assert 1.3 < ratio < 1.8  # Should be sub-linear

    def test_t_slip_03_max_cap_50_bps(self):
        """T_SLIP_03: Slippage capped at 50 bps."""
        slippage = estimate_slippage(
            position_size_usd=1000000,
            bid_depth_usd=1000,
            ask_depth_usd=1000,
            side="long",
        )

        assert slippage <= SLIPPAGE_MAX_BPS

    def test_zero_position(self):
        """Zero size returns zero slippage."""
        slippage = estimate_slippage(
            position_size_usd=0,
            bid_depth_usd=100000,
            ask_depth_usd=100000,
            side="long",
        )

        assert slippage == 0.0


class TestEstimateSlippageSimple:
    """Tests for estimate_slippage_simple."""

    def test_simple_uses_average_depth(self):
        """Simple version uses single depth value."""
        slippage = estimate_slippage_simple(
            position_size_usd=10000,
            depth_usd=100000,
        )

        # ratio = 0.1, slippage = min(0.1^0.7 * 5, 50) = min(0.997, 50) = 0.997
        assert slippage > 0
        assert slippage < 1

    def test_zero_depth(self):
        """Zero depth returns max slippage."""
        slippage = estimate_slippage_simple(10000, 0)
        assert slippage == SLIPPAGE_MAX_BPS


class TestDepthRequired:
    """Tests for depth_required_for_target_slippage."""

    def test_depth_for_5_bps(self):
        """Calculate depth needed for 5 bps slippage."""
        # With SCALE=5: (5/5)^(1/0.7) = 1^1.43 = 1.0
        # depth = 10000 / 1.0 = 10000
        depth = depth_required_for_target_slippage(
            position_size_usd=10000,
            target_slippage_bps=5,
        )

        assert 9000 < depth < 11000

    def test_depth_for_zero_slippage(self):
        """Zero target requires zero depth (edge case)."""
        depth = depth_required_for_target_slippage(
            position_size_usd=10000,
            target_slippage_bps=0,
        )

        assert depth == 0.0


class TestCalculateExecutionPrice:
    """Tests for calculate_execution_price."""

    def test_long_increases_price(self):
        """Long execution price higher than mid."""
        price = calculate_execution_price(
            mid_price=100,
            slippage_bps=10,  # 10 bps = 0.1%
            side="long",
        )

        assert price > 100
        assert price == pytest.approx(100.1, abs=0.01)

    def test_short_decreases_price(self):
        """Short execution price lower than mid."""
        price = calculate_execution_price(
            mid_price=100,
            slippage_bps=10,
            side="short",
        )

        assert price < 100
        assert price == pytest.approx(99.9, abs=0.01)
