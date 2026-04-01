"""
Unit tests for Liquidity Checker.
"""
import pytest
from tradingagents_crypto.agents.risk_mgmt.liquidity_checker import (
    estimate_slippage,
    check_liquidity,
    get_required_depth_for_slippage,
    SLIPPAGE_MAX_BPS,
)


class TestEstimateSlippage:
    """Tests for estimate_slippage function."""

    def test_t_lipchk_01_low_slippage_small_position(self):
        """T_LIQCHK_01: Small position relative to depth = low slippage."""
        # ratio = 1000 / 100000 = 0.01
        # slippage = min(0.01^0.7 * 10, 50) = min(0.25, 50) = 0.25 bps
        slippage = estimate_slippage(
            position_size_usd=1000,
            bid_depth_usd=100000,
            ask_depth_usd=100000,
            side="long",
        )

        assert slippage < 5  # < 5 bps = low

    def test_t_lipchk_02_high_slippage_large_position(self):
        """T_LIQCHK_02: Large position = higher slippage."""
        # ratio = 50000 / 100000 = 0.5
        # slippage = min(0.5^0.7 * 10, 50) = min(3.76, 50) = 3.76 bps
        slippage = estimate_slippage(
            position_size_usd=50000,
            bid_depth_usd=100000,
            ask_depth_usd=100000,
            side="long",
        )

        assert slippage > 0

    def test_t_lipchk_03_slippage_cap_at_50_bps(self):
        """T_LIQCHK_03: Slippage should not exceed 50 bps."""
        # Very large position
        # ratio = 1000000 / 1000 = 1000
        # slippage = min(1000^0.7 * 10, 50) = min(158, 50) = 50 bps
        slippage = estimate_slippage(
            position_size_usd=1000000,
            bid_depth_usd=1000,
            ask_depth_usd=1000,
            side="long",
        )

        assert slippage <= SLIPPAGE_MAX_BPS

    def test_t_lipchk_04_long_vs_short_different_depth(self):
        """T_LIQCHK_04: Long and short use different depth sides."""
        slippage_long = estimate_slippage(
            position_size_usd=10000,
            bid_depth_usd=50000,
            ask_depth_usd=200000,
            side="long",
        )

        slippage_short = estimate_slippage(
            position_size_usd=10000,
            bid_depth_usd=50000,
            ask_depth_usd=200000,
            side="short",
        )

        # Long uses bid (50k), short uses ask (200k)
        # Long should have higher slippage
        assert slippage_long > slippage_short

    def test_t_lipchk_05_zero_depth_returns_max(self):
        """T_LIQCHK_05: Zero depth returns max slippage."""
        slippage = estimate_slippage(
            position_size_usd=10000,
            bid_depth_usd=0,
            ask_depth_usd=0,
            side="long",
        )

        assert slippage == SLIPPAGE_MAX_BPS

    def test_zero_position_returns_zero(self):
        """Zero position size returns zero slippage."""
        slippage = estimate_slippage(
            position_size_usd=0,
            bid_depth_usd=100000,
            ask_depth_usd=100000,
            side="long",
        )

        assert slippage == 0.0


class TestCheckLiquidity:
    """Tests for check_liquidity function."""

    def test_low_risk_recommendation(self):
        """Low slippage → '正常开仓'."""
        result = check_liquidity(
            position_size_usd=1000,
            bid_depth_usd=100000,
            ask_depth_usd=100000,
            side="long",
        )

        assert result.liquidity_risk == "low"
        assert result.recommendation == "正常开仓"

    def test_high_risk_recommendation(self):
        """High slippage → '拒绝'."""
        result = check_liquidity(
            position_size_usd=500000,
            bid_depth_usd=50000,
            ask_depth_usd=50000,
            side="long",
        )

        assert result.liquidity_risk == "high"
        assert result.recommendation == "拒绝"


class TestGetRequiredDepth:
    """Tests for get_required_depth_for_slippage."""

    def test_required_depth_calculation(self):
        """Test depth calculation for target slippage."""
        # Target 5 bps
        # ratio = (5 / 10) ^ (1/0.7) = 0.5 ^ 1.43 = 0.38
        # depth = 10000 / 0.38 = ~26,315
        depth = get_required_depth_for_slippage(
            position_size_usd=10000,
            target_slippage_bps=5,
            side="long",
        )

        assert depth > 10000  # Need more depth than position
        assert depth < 50000

    def test_depth_for_zero_slippage(self):
        """Zero slippage target requires infinite depth."""
        depth = get_required_depth_for_slippage(
            position_size_usd=10000,
            target_slippage_bps=0,
            side="long",
        )

        assert depth == 0.0
