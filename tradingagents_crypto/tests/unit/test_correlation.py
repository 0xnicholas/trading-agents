"""
Unit tests for correlation module.
"""
import pytest
from tradingagents_crypto.dataflows.macro.correlation import (
    calc_pearson_correlation,
    interpret_correlation,
)


class TestCalcPearsonCorrelation:
    """Tests for Pearson correlation calculation."""

    def test_perfect_positive_correlation(self):
        """Test perfect positive correlation."""
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        corr = calc_pearson_correlation(x, y)
        assert corr == pytest.approx(1.0, abs=0.01)

    def test_perfect_negative_correlation(self):
        """Test perfect negative correlation."""
        x = [1, 2, 3, 4, 5]
        y = [10, 8, 6, 4, 2]
        corr = calc_pearson_correlation(x, y)
        assert corr == pytest.approx(-1.0, abs=0.01)

    def test_zero_correlation(self):
        """Test zero correlation."""
        x = [1, 2, 3, 4, 5]
        y = [10, 10, 10, 10, 10]
        corr = calc_pearson_correlation(x, y)
        assert corr == pytest.approx(0.0, abs=0.01)

    def test_different_length_returns_zero(self):
        """Test different length series returns 0."""
        x = [1, 2, 3]
        y = [1, 2, 3, 4, 5]
        corr = calc_pearson_correlation(x, y)
        assert corr == 0.0

    def test_single_value_returns_zero(self):
        """Test single value returns 0."""
        x = [1]
        y = [2]
        corr = calc_pearson_correlation(x, y)
        assert corr == 0.0

    def test_moderate_positive_correlation(self):
        """Test moderate positive correlation."""
        x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        y = [2, 4, 3, 5, 7, 6, 8, 10, 9, 11]
        corr = calc_pearson_correlation(x, y)
        assert corr > 0.5  # Should be positively correlated


class TestInterpretCorrelation:
    """Tests for correlation interpretation."""

    def test_high_correlation_risk_on(self):
        """Test high correlation = risk_on regime."""
        result = interpret_correlation(0.85, 0.80)
        assert result["regime"] == "risk_on"
        assert result["confidence"] == 0.8

    def test_low_correlation_diverge(self):
        """Test low correlation = divergence."""
        result = interpret_correlation(0.3, 0.4)
        assert result["regime"] == "分化"
        assert result["confidence"] == 0.8

    def test_altcoin_rotation(self):
        """Test SOL decoupling = altcoin rotation."""
        result = interpret_correlation(0.7, 0.4)  # SOL much lower than ETH
        assert result["regime"] == "altcoin_rotation"
        assert result["confidence"] == 0.8
