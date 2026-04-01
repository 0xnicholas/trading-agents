"""
Unit tests for Exposure Monitor.
"""
import pytest
from tradingagents_crypto.agents.risk_mgmt.exposure_monitor import (
    check_exposure,
    get_max_position_size,
    Position,
    ExposureCheckResult,
    MAX_SINGLE_ASSET_EXPOSURE,
    MAX_ONE_WAY_EXPOSURE,
)


class TestCheckExposure:
    """Tests for check_exposure function."""

    def test_t_exp_01_single_asset_over_limit(self):
        """T_EXP_01: Single asset exceeds 20% limit."""
        positions = [
            Position(
                symbol="BTC",
                side="long",
                size_usd=25000,  # 25% of 100k
                entry_price=50000,
                current_price=50000,
            )
        ]

        result = check_exposure(positions, total_equity=100000)

        assert not result.approved
        assert any("单币种上限" in v.rule for v in result.violations)

    def test_t_exp_02_one_way_exposure_over_60_percent(self):
        """T_EXP_02: Same-direction exposure exceeds 60%."""
        positions = [
            Position(symbol="BTC", side="long", size_usd=25000, entry_price=50000, current_price=50000),
            Position(symbol="ETH", side="long", size_usd=25000, entry_price=3000, current_price=3000),
            Position(symbol="SOL", side="long", size_usd=15000, entry_price=100, current_price=100),
            # Total long: 65000 / 100000 = 65% > 60%
        ]

        result = check_exposure(positions, total_equity=100000)

        assert not result.approved
        assert any("单向暴露上限" in v.rule for v in result.violations)

    def test_t_exp_03_all_rules_pass(self):
        """T_EXP_03: Well-diversified portfolio passes."""
        positions = [
            Position(symbol="BTC", side="long", size_usd=15000, entry_price=50000, current_price=50000),
            Position(symbol="ETH", side="long", size_usd=15000, entry_price=3000, current_price=3000),
            Position(symbol="SOL", side="long", size_usd=5000, entry_price=100, current_price=100),
            Position(symbol="AVAX", side="long", size_usd=5000, entry_price=35, current_price=35),
        ]

        result = check_exposure(positions, total_equity=100000)

        assert result.approved
        assert len(result.violations) == 0

    def test_t_exp_04_new_position_causes_reject(self):
        """T_EXP_04: Adding new position would exceed limit."""
        existing = [
            Position(symbol="BTC", side="long", size_usd=18000, entry_price=50000, current_price=50000),
            Position(symbol="ETH", side="long", size_usd=18000, entry_price=3000, current_price=3000),
            # Already 36%, new position would push over 40%
        ]

        new_pos = Position(
            symbol="SOL",
            side="long",
            size_usd=10000,  # Would make total 46%
            entry_price=100,
            current_price=100,
        )

        result = check_exposure(existing, total_equity=100000, new_position=new_pos)

        assert not result.approved

    def test_t_exp_05_hedged_position_within_limits(self):
        """T_EXP_05: Hedged positions don't count toward limit."""
        # Long BTC 25% + Short BTC 25% = net 0%, gross 50%
        positions = [
            Position(symbol="BTC", side="long", size_usd=25000, entry_price=50000, current_price=50000),
            Position(symbol="BTC", side="short", size_usd=25000, entry_price=50000, current_price=50000),
        ]

        result = check_exposure(positions, total_equity=100000)

        # Net long = 0, should pass
        assert result.approved

    def test_t_exp_06_diversity_warning(self):
        """T_EXP_06: Less than 3 assets triggers warning."""
        positions = [
            Position(symbol="BTC", side="long", size_usd=20000, entry_price=50000, current_price=50000),
            Position(symbol="ETH", side="long", size_usd=20000, entry_price=3000, current_price=3000),
            # Only 2 symbols - should warn
        ]

        result = check_exposure(positions, total_equity=100000)

        assert result.approved  # Should still approve
        assert any("分散度" in w.rule for w in result.warnings)

    def test_t_exp_07_leverage_over_limit(self):
        """T_EXP_07: Position with leverage > 20x rejected."""
        positions = [
            Position(
                symbol="BTC",
                side="long",
                size_usd=10000,
                entry_price=50000,
                current_price=50000,
                leverage=25,  # Over 20x limit
            )
        ]

        result = check_exposure(positions, total_equity=100000)

        assert not result.approved
        assert any("最大杠杆" in v.rule for v in result.violations)

    def test_zero_equity_rejects_all(self):
        """Zero equity rejects all positions."""
        positions = [
            Position(symbol="BTC", side="long", size_usd=1000, entry_price=50000, current_price=50000),
        ]

        result = check_exposure(positions, total_equity=0)

        assert not result.approved


class TestGetMaxPositionSize:
    """Tests for get_max_position_size."""

    def test_max_position_calculation(self):
        """Test max position size calculation."""
        max_size = get_max_position_size(
            total_equity=100000,
            current_exposure=10000,
            max_exposure_pct=0.20,
        )

        # 20% of 100k = 20k, current = 10k, available = 10k
        assert max_size == 10000

    def test_max_position_zero_available(self):
        """Test when already at limit."""
        max_size = get_max_position_size(
            total_equity=100000,
            current_exposure=20000,
            max_exposure_pct=0.20,
        )

        assert max_size == 0.0

    def test_max_position_no_existing(self):
        """Test with no existing exposure."""
        max_size = get_max_position_size(
            total_equity=100000,
            current_exposure=0,
        )

        # 20% of 100k = 20k
        assert max_size == 20000
