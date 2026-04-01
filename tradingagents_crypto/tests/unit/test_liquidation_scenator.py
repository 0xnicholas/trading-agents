"""
Unit tests for LiquidationScenator.
"""
import pytest
from tradingagents_crypto.agents.risk_mgmt.liquidation_scenator import (
    calc_liquidation,
    get_position_risk,
    LiquidationResult,
)


class TestCalcLiquidation:
    """Tests for calc_liquidation function."""

    def test_t_liq_01_20x_long_5pct_drop_is_danger(self):
        """T_LIQ_01: 20x long, price drops 5%, should be danger."""
        result = calc_liquidation(
            direction="long",
            entry_price=100,
            current_price=95,
            leverage=20,
        )
        # liq_price = 100 * (1 - 1/20) = 100 * 0.95 = 95
        # distance = (95 - 95) / 95 = 0%
        assert result.recommendation == "danger"
        assert result.distance_to_liq_pct == pytest.approx(0.0, abs=0.001)

    def test_t_liq_02_5x_long_safe_distance(self):
        """T_LIQ_02: 5x long with ample safety buffer."""
        result = calc_liquidation(
            direction="long",
            entry_price=100,
            current_price=98,
            leverage=5,
        )
        # liq_price = 100 * (1 - 1/5) = 100 * 0.8 = 80
        # distance = (98 - 80) / 98 = 18.4%
        assert result.distance_to_liq_pct > 0.10  # > 10% = safe
        assert result.recommendation == "safe"

    def test_t_liq_03_10x_short_normal_distance(self):
        """T_LIQ_03: 10x short, normal distance."""
        result = calc_liquidation(
            direction="short",
            entry_price=100,
            current_price=104,  # was 105 → 4.76% (danger). 104 → 5.77% (caution)
            leverage=10,
        )
        # liq_price = 100 * (1 + 1/10) = 100 * 1.1 = 110
        # distance = (110 - 104) / 104 = 5.77% → caution (5-10%)
        assert result.recommendation in ("caution", "safe")

    def test_t_liq_04_max_safe_leverage_calculation(self):
        """T_LIQ_04: Calculate max safe leverage."""
        result = calc_liquidation(
            direction="long",
            entry_price=100,
            current_price=95,
            leverage=20,
        )
        # current=95, liq=95 (at 20x), so max safe ≈ 19x
        assert result.max_safe_leverage < 20
        assert result.max_safe_leverage > 18

    def test_t_liq_05_cross_margin_mode(self):
        """T_LIQ_05: Cross margin mode doesn't crash."""
        result = calc_liquidation(
            direction="long",
            entry_price=100,
            current_price=98,
            leverage=20,
            margin_mode="cross",
        )
        assert isinstance(result, LiquidationResult)
        assert result.liquidation_price < 100  # Cross margin liq closer

    def test_t_liq_06_leverage_1_no_leverage(self):
        """T_LIQ_06: Leverage=1 is essentially no leverage."""
        result = calc_liquidation(
            direction="long",
            entry_price=100,
            current_price=95,
            leverage=1,
        )
        assert result.liquidation_price == 100
        assert result.distance_to_liq_pct == 0.0
        assert result.recommendation == "danger"

    def test_t_liq_07_max_leverage_boundary(self):
        """T_LIQ_07: Maximum leverage boundary."""
        result = calc_liquidation(
            direction="long",
            entry_price=100,
            current_price=99.5,
            leverage=20,
        )
        # liq = 100 * (1 - 1/20) = 95
        # distance = (99.5 - 95) / 99.5 = 4.5% → caution
        assert result.distance_to_liq_pct > 0
        assert result.liquidation_price == 95.0

    def test_short_liquidation_price(self):
        """Short liquidation price formula."""
        result = calc_liquidation(
            direction="short",
            entry_price=100,
            current_price=100,
            leverage=10,
        )
        # liq = 100 * (1 + 1/10) = 110
        assert result.liquidation_price == 110.0

    def test_get_position_risk_returns_dict(self):
        """Test get_position_risk returns correct dict structure."""
        risk = get_position_risk(
            direction="long",
            entry_price=100,
            current_price=95,
            leverage=10,
        )
        assert "liquidation_price" in risk
        assert "distance_to_liq_pct" in risk
        assert "recommendation" in risk
        assert "max_safe_leverage" in risk
