"""
M3.5: Reporting System Tests.

Tests for markdown report generation and visualization.
"""
import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta

from tradingagents_crypto.backtest.backtest_engine import BacktestEngine, BacktestConfig, TradeSignal
from tradingagents_crypto.backtest.reporting import (
    generate_markdown_report,
    generate_equity_curve_base64,
    generate_drawdown_curve_base64,
    generate_monthly_returns_heatmap,
)


def generate_test_equity(days: int = 100, seed: int = 42) -> pd.Series:
    """Generate synthetic equity curve."""
    np.random.seed(seed)
    n = days * 24
    returns = np.random.normal(0.0001, 0.02, n)
    equity = 100000 * np.exp(np.cumsum(returns))
    index = pd.date_range(start="2024-01-01", periods=n, freq="h")
    return pd.Series(equity, index=index)


def generate_test_trades():
    """Generate synthetic trade list."""
    from tradingagents_crypto.backtest.backtest_engine import Trade
    return [
        Trade(
            entry_time=3600,
            exit_time=7200,
            symbol="BTC",
            side="long",
            size=10000,
            entry_price=50000,
            exit_price=50500,
            entry_reason="signal",
            pnl=500,
            commission=10,
            slippage_cost=5,
            funding_cost=0,
            realized_pnl=485,
        ),
        Trade(
            entry_time=7200,
            exit_time=14400,
            symbol="BTC",
            side="long",
            size=10000,
            entry_price=50500,
            exit_price=50000,
            entry_reason="signal",
            pnl=-500,
            commission=10,
            slippage_cost=5,
            funding_cost=0,
            realized_pnl=-515,
        ),
    ]


class TestMarkdownReport:
    """Test markdown report generation."""

    def test_report_contains_summary(self):
        """Report contains key metrics summary."""
        candles = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=100, freq="h"),
            "open": [50000] * 100,
            "high": [50500] * 100,
            "low": [49500] * 100,
            "close": [50000 + i for i in range(100)],
            "volume": [1000] * 100,
        })

        def strategy(timestamp, candles, funding, oi, indicators):
            return TradeSignal(action="hold")

        engine = BacktestEngine(BacktestConfig(initial_capital=100000))
        result = engine.run(strategy, candles)

        report = generate_markdown_report(
            result,
            strategy_name="Test Strategy",
            include_equity_chart=False,
            include_drawdown_chart=False,
            include_monthly_heatmap=False,
        )

        assert "Backtest Report" in report
        assert "Total Return" in report
        assert "Sharpe Ratio" in report
        assert "Max Drawdown" in report

    def test_report_contains_confidence(self):
        """Report contains data quality and confidence section."""
        candles = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=100, freq="h"),
            "open": [50000] * 100,
            "high": [50500] * 100,
            "low": [49500] * 100,
            "close": [50000 + i for i in range(100)],
            "volume": [1000] * 100,
        })

        def strategy(timestamp, candles, funding, oi, indicators):
            return TradeSignal(action="hold")

        engine = BacktestEngine(BacktestConfig(initial_capital=100000))
        result = engine.run(strategy, candles)

        report = generate_markdown_report(
            result,
            strategy_name="Test",
            include_equity_chart=False,
        )

        assert "Confidence" in report or "confidence" in report.lower()

    def test_report_with_trades(self):
        """Report includes trade log summary when trades exist."""
        equity = generate_test_equity(days=10)
        trades = generate_test_trades()

        from tradingagents_crypto.backtest.backtest_engine import BacktestMetrics, BacktestConfidence
        from tradingagents_crypto.backtest.backtest_engine import BacktestResult

        result = BacktestResult(
            equity_curve=equity,
            trades=trades,
            metrics=BacktestMetrics(
                total_return=0.05,
                sharpe_ratio=1.2,
                max_drawdown=-0.1,
                calmar_ratio=0.5,
                win_rate=0.5,
                profit_factor=1.2,
                avg_trade_duration_hours=2.0,
                total_trades=2,
                equity_final=105000,
                equity_peak=110000,
            ),
            confidence=BacktestConfidence(
                data_completeness=0.98,
                slippage_model="estimated",
                funding_history="real",
                leverage_effects="simplified",
            ),
            metadata={
                "initial_capital": 100000,
                "start_date": "2024-01-01",
                "end_date": "2024-01-10",
                "num_bars": 240,
            },
        )

        report = generate_markdown_report(
            result,
            strategy_name="Test with Trades",
            include_equity_chart=False,
            include_drawdown_chart=False,
        )

        assert "Trade Log" in report or "trade" in report.lower()


class TestChartGeneration:
    """Test chart generation functions."""

    def test_equity_curve_chart(self):
        """Equity curve generates base64 PNG."""
        equity = generate_test_equity(days=30)

        chart = generate_equity_curve_base64(equity)

        assert chart is not None
        assert len(chart) > 1000  # Should be substantial
        assert chart.startswith("iVBOR")  # PNG header

    def test_drawdown_chart(self):
        """Drawdown curve generates base64 PNG."""
        equity = generate_test_equity(days=30)

        chart = generate_drawdown_curve_base64(equity)

        assert chart is not None
        assert len(chart) > 100

    def test_monthly_heatmap(self):
        """Monthly returns heatmap for sufficient data."""
        equity = generate_test_equity(days=90)  # Need ~3 months

        chart = generate_monthly_returns_heatmap(equity)

        # May return None if insufficient data
        # Just verify it runs without error
        assert chart is None or len(chart) > 0


class TestReportOutput:
    """Test report output options."""

    def test_report_saves_to_file(self, tmp_path):
        """Report can be saved to file."""
        equity = generate_test_equity(days=10)

        from tradingagents_crypto.backtest.backtest_engine import (
            BacktestResult, BacktestMetrics, BacktestConfidence
        )

        result = BacktestResult(
            equity_curve=equity,
            trades=[],
            metrics=BacktestMetrics(
                total_return=0.05,
                sharpe_ratio=1.2,
                max_drawdown=-0.1,
                calmar_ratio=0.5,
                win_rate=0.5,
                profit_factor=1.2,
                avg_trade_duration_hours=0,
                total_trades=0,
                equity_final=105000,
                equity_peak=110000,
            ),
            confidence=BacktestConfidence(),
            metadata={"initial_capital": 100000},
        )

        output_file = tmp_path / "report.md"

        report = generate_markdown_report(
            result,
            strategy_name="Test",
            output_path=str(output_file),
            include_equity_chart=False,
            include_drawdown_chart=False,
        )

        assert output_file.exists()
        content = output_file.read_text()
        assert "Backtest Report" in content
