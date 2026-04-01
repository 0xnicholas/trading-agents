"""
Unit tests for Funding Simulator.
"""
import pytest
from tradingagents_crypto.backtest.funding_simulator import (
    calc_funding_pnl,
    calc_funding_cost,
    annualize_funding_rate,
    format_funding_rate,
)


class TestCalcFundingPNL:
    """Tests for calc_funding_pnl function."""

    def test_t_fund_01_positive_rate_long_pays(self):
        """T_FUND_01: Positive rate, long position pays."""
        # rate=0.0001 (0.01%), value=10000
        # long: pnl = -0.0001 * 10000 = -1
        pnl = calc_funding_pnl(
            position_side="long",
            position_value=10000,
            funding_rate=0.0001,
        )

        assert pnl < 0  # Long pays

    def test_t_fund_02_positive_rate_short_receives(self):
        """T_FUND_02: Positive rate, short position receives."""
        # rate=0.0001 (0.01%), value=10000
        # short: pnl = 0.0001 * 10000 = +1
        pnl = calc_funding_pnl(
            position_side="short",
            position_value=10000,
            funding_rate=0.0001,
        )

        assert pnl > 0  # Short receives

    def test_t_fund_03_negative_rate_long_receives(self):
        """T_FUND_03: Negative rate, long position receives."""
        # rate=-0.0001, value=10000
        # long: pnl = -(-0.0001) * 10000 = +1
        pnl = calc_funding_pnl(
            position_side="long",
            position_value=10000,
            funding_rate=-0.0001,
        )

        assert pnl > 0  # Long receives when rate is negative

    def test_t_fund_04_negative_rate_short_pays(self):
        """T_FUND_04: Negative rate, short position pays."""
        # rate=-0.0001, value=10000
        # short: pnl = -0.0001 * 10000 = -1
        pnl = calc_funding_pnl(
            position_side="short",
            position_value=10000,
            funding_rate=-0.0001,
        )

        assert pnl < 0  # Short pays when rate is negative

    def test_t_fund_05_zero_rate(self):
        """T_FUND_05: Zero funding rate."""
        pnl = calc_funding_pnl(
            position_side="long",
            position_value=10000,
            funding_rate=0.0,
        )

        assert pnl == 0.0

    def test_t_fund_06_all_directions_correct_signs(self):
        """T_FUND_06: Verify all 4 combinations have correct signs."""
        rate = 0.0001
        value = 10000

        long_pos = calc_funding_pnl("long", value, rate)
        short_pos = calc_funding_pnl("short", value, rate)
        long_neg = calc_funding_pnl("long", value, -rate)
        short_neg = calc_funding_pnl("short", value, -rate)

        # Positive rate: long<0, short>0
        assert long_pos < 0
        assert short_pos > 0

        # Negative rate: long>0, short<0
        assert long_neg > 0
        assert short_neg < 0


class TestCalcFundingCost:
    """Tests for calc_funding_cost over time period."""

    def test_funding_cost_8_hours(self):
        """8 hours = 1 period."""
        cost = calc_funding_cost(
            position_side="long",
            position_value=10000,
            funding_rate=0.0001,
            hours=8,
        )

        # 1 period: -0.0001 * 10000 = -1
        assert cost == pytest.approx(-1.0, abs=0.01)

    def test_funding_cost_24_hours(self):
        """24 hours = 3 periods."""
        cost = calc_funding_cost(
            position_side="long",
            position_value=10000,
            funding_rate=0.0001,
            hours=24,
        )

        # 3 periods: -0.0001 * 10000 * 3 = -3
        assert cost == pytest.approx(-3.0, abs=0.01)


class TestAnnualizeFundingRate:
    """Tests for annualize_funding_rate."""

    def test_annualize_positive_rate(self):
        """Annualize 0.01% per 8h."""
        # 0.0001 * 3 * 365 = 0.1095 = 10.95%
        rate = annualize_funding_rate(0.0001)

        assert rate == pytest.approx(0.1095, abs=0.001)  # ~10.95%

    def test_annualize_zero_rate(self):
        """Zero rate annualizes to zero."""
        rate = annualize_funding_rate(0.0)

        assert rate == 0.0


class TestFormatFundingRate:
    """Tests for format_funding_rate."""

    def test_format_rate(self):
        """Format rate correctly."""
        formatted = format_funding_rate(0.0001)

        assert "0.0100%" in formatted
        assert "annualized" in formatted
