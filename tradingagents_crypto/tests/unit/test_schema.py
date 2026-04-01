"""
Unit tests for agent schemas.
"""
import pytest
from pydantic import ValidationError

from agents.schema import (
    HyperliquidPerpReport,
    HyperliquidPerpSignals,
    HyperliquidPerpMetrics,
    FundingSignal,
    OITrend,
    OrderbookImbalance,
    VolumeAnomaly,
    VolatilitySignal,
    TrendSignal,
    TradeSignal,
    RiskReport,
    FinalDecision,
)


class TestFundingSignal:
    """Tests for FundingSignal schema."""

    def test_valid_signal(self):
        """Valid funding signal passes."""
        signal = FundingSignal(
            value=0.0001,
            annualized=0.1095,
            direction="positive (longs pay)",
            verdict="normal",
        )
        assert signal.value == 0.0001

    def test_invalid_verdict(self):
        """Invalid verdict raises error."""
        with pytest.raises(ValidationError):
            FundingSignal(
                value=0.0001,
                annualized=0.1095,
                direction="positive (longs pay)",
                verdict="invalid",
            )


class TestHyperliquidPerpReport:
    """Tests for HyperliquidPerpReport schema."""

    def test_valid_report(self):
        """Valid report passes."""
        report = HyperliquidPerpReport(
            summary="Short-term bullish",
            direction="bullish",
            confidence=0.75,
            signals=HyperliquidPerpSignals(
                funding_rate=FundingSignal(
                    value=0.0001,
                    annualized=0.1095,
                    direction="positive (longs pay)",
                    verdict="normal",
                ),
                oi_trend=OITrend(
                    current=500_000_000.0,
                    change_24h_pct=5.2,
                    direction="expanding",
                    verdict="bullish",
                ),
                orderbook_imbalance=OrderbookImbalance(
                    bid_depth=1_500_000.0,
                    ask_depth=1_200_000.0,
                    imbalance_ratio=1.25,
                    verdict="bullish",
                ),
                volume_anomaly=VolumeAnomaly(
                    volume_24h=1_500_000_000.0,
                    volume_ma7=1_300_000_000.0,
                    ratio=1.15,
                    verdict="normal",
                ),
                volatility=VolatilitySignal(
                    atr_24h=500.0,
                    atr_pct=0.0075,
                    position="medium",
                ),
                trend_4h=TrendSignal(
                    direction="bullish",
                    ma_cross="above_ma",
                ),
                trend_1d=TrendSignal(
                    direction="neutral",
                    ma_cross="above_ma",
                ),
            ),
            metrics=HyperliquidPerpMetrics(
                mark_price=67_200.0,
                index_price=67_180.0,
                funding_rate=0.0001,
                open_interest_usd=500_000_000.0,
                volume_24h=1_500_000_000.0,
                rsi=58.5,
                atr=500.0,
                macd=150.0,
                macd_signal=120.0,
                boll_upper=68_000.0,
                boll_lower=66_000.0,
            ),
            narrative="Detailed analysis..." * 20,
        )
        assert report.direction == "bullish"
        assert report.confidence == 0.75

    def test_invalid_direction(self):
        """Invalid direction raises error."""
        with pytest.raises(ValidationError):
            HyperliquidPerpReport(
                summary="Test",
                direction="invalid_direction",
                confidence=0.75,
                signals=_valid_signals(),
                metrics=_valid_metrics(),
                narrative="Detailed analysis..." * 20,
            )

    def test_confidence_out_of_range(self):
        """Confidence > 1.0 raises error."""
        with pytest.raises(ValidationError):
            HyperliquidPerpReport(
                summary="Test",
                direction="bullish",
                confidence=1.5,
                signals=_valid_signals(),
                metrics=_valid_metrics(),
                narrative="Detailed analysis..." * 20,
            )

    def test_summary_too_long(self):
        """Summary > 200 chars raises error."""
        with pytest.raises(ValidationError):
            HyperliquidPerpReport(
                summary="x" * 201,
                direction="bullish",
                confidence=0.75,
                signals=_valid_signals(),
                metrics=_valid_metrics(),
                narrative="Detailed analysis..." * 20,
            )


class TestTradeSignal:
    """Tests for TradeSignal schema."""

    def test_valid_long(self):
        """Valid long signal."""
        signal = TradeSignal(
            action="long",
            size_pct=0.5,
            leverage=10,
            entry_reason="Funding rate low",
            risk_adjusted=True,
        )
        assert signal.action == "long"

    def test_invalid_leverage(self):
        """Leverage > 20 raises error."""
        with pytest.raises(ValidationError):
            TradeSignal(
                action="long",
                size_pct=0.5,
                leverage=25,
                entry_reason="Test",
                risk_adjusted=True,
            )

    def test_size_out_of_range(self):
        """size_pct > 1.0 raises error."""
        with pytest.raises(ValidationError):
            TradeSignal(
                action="long",
                size_pct=1.5,
                leverage=10,
                entry_reason="Test",
                risk_adjusted=True,
            )


class TestRiskReport:
    """Tests for RiskReport schema."""

    def test_approved_with_warnings(self):
        """Can be approved with warnings."""
        report = RiskReport(
            approved=True,
            warnings=["High volatility"],
            adjustments={"leverage": 3},
            recommendation="caution",
        )
        assert report.approved is True
        assert len(report.warnings) == 1


class TestFinalDecision:
    """Tests for FinalDecision schema."""

    def test_valid_hold(self):
        """Valid hold decision."""
        decision = FinalDecision(
            action="hold",
            size_pct=0.0,
            leverage=1,
            reason="Uncertain market",
            risk_checks=RiskReport(
                approved=True,
                recommendation="safe",
            ),
        )
        assert decision.action == "hold"


# Helper functions

def _valid_signals() -> HyperliquidPerpSignals:
    """Create valid signals object."""
    return HyperliquidPerpSignals(
        funding_rate=FundingSignal(
            value=0.0001,
            annualized=0.1095,
            direction="positive (longs pay)",
            verdict="normal",
        ),
        oi_trend=OITrend(
            current=500_000_000.0,
            change_24h_pct=5.2,
            direction="expanding",
            verdict="bullish",
        ),
        orderbook_imbalance=OrderbookImbalance(
            bid_depth=1_500_000.0,
            ask_depth=1_200_000.0,
            imbalance_ratio=1.25,
            verdict="bullish",
        ),
        volume_anomaly=VolumeAnomaly(
            volume_24h=1_500_000_000.0,
            volume_ma7=1_300_000_000.0,
            ratio=1.15,
            verdict="normal",
        ),
        volatility=VolatilitySignal(
            atr_24h=500.0,
            atr_pct=0.0075,
            position="medium",
        ),
        trend_4h=TrendSignal(
            direction="bullish",
            ma_cross="above_ma",
        ),
        trend_1d=TrendSignal(
            direction="neutral",
            ma_cross="above_ma",
        ),
    )


def _valid_metrics() -> HyperliquidPerpMetrics:
    """Create valid metrics object."""
    return HyperliquidPerpMetrics(
        mark_price=67_200.0,
        index_price=67_180.0,
        funding_rate=0.0001,
        open_interest_usd=500_000_000.0,
        volume_24h=1_500_000_000.0,
        rsi=58.5,
        atr=500.0,
        macd=150.0,
        macd_signal=120.0,
        boll_upper=68_000.0,
        boll_lower=66_000.0,
    )
