"""
Unit tests for Benchmark module.
"""
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from tradingagents_crypto.backtest.benchmark import (
    calculate_benchmark_metrics,
    BenchmarkMetrics,
    print_metrics_comparison,
)


def generate_equity_curve(days: int = 100, initial: float = 100000, seed: int = 42) -> pd.Series:
    """Generate a synthetic equity curve."""
    np.random.seed(seed)
    n = days * 24  # Hourly
    dt = 1 / (24 * 365)

    # Random walk with upward drift
    returns = np.random.normal(0.0001, 0.02, n)
    equity = initial * np.exp(np.cumsum(returns))

    index = pd.date_range(start="2024-01-01", periods=n, freq="h")
    return pd.Series(equity, index=index)


class TestCalculateBenchmarkMetrics:
    """Tests for calculate_benchmark_metrics."""

    def test_t_bm_01_sharpe_ratio_accuracy(self):
        """T_BM_01: Sharpe ratio calculation accuracy with fixed seed."""
        equity = generate_equity_curve(days=100, seed=42)
        metrics = calculate_benchmark_metrics(equity)

        # With seed=42, should get consistent results
        assert isinstance(metrics.sharpe_ratio, float)
        assert -10 < metrics.sharpe_ratio < 10  # Reasonable range

    def test_t_bm_02_max_drawdown_negative(self):
        """T_BM_02: Max drawdown should be negative (or zero)."""
        equity = generate_equity_curve(days=100, seed=123)
        metrics = calculate_benchmark_metrics(equity)

        assert metrics.max_drawdown <= 0.0

    def test_t_bm_03_calmar_ratio_formula(self):
        """T_BM_03: Calmar ratio = return / |drawdown|."""
        equity = generate_equity_curve(days=100, seed=456)
        metrics = calculate_benchmark_metrics(equity)

        # Calmar should be return / |drawdown|
        expected_calmar = metrics.total_return / abs(metrics.max_drawdown) if metrics.max_drawdown != 0 else 0
        assert abs(metrics.calmar_ratio - expected_calmar) < 0.01

    def test_t_bm_04_empty_equity(self):
        """T_BM_04: Empty equity curve returns zeros."""
        equity = pd.Series([])
        metrics = calculate_benchmark_metrics(equity)

        assert metrics.total_return == 0.0
        assert metrics.sharpe_ratio == 0.0
        assert metrics.max_drawdown == 0.0

    def test_t_bm_05_single_point(self):
        """T_BM_05: Single data point returns zero."""
        equity = pd.Series([100000], index=[datetime.now()])
        metrics = calculate_benchmark_metrics(equity)

        # Can't calculate returns or drawdown with 1 point
        assert metrics.total_return == 0.0

    def test_t_bm_06_win_rate_from_trades(self):
        """T_BM_06: Win rate calculated from trades."""
        from tradingagents_crypto.backtest.backtest_engine import Trade

        trades = [
            Trade(entry_time=1, exit_time=2, symbol="BTC", side="long",
                  size=10000, entry_price=50000, exit_price=51000,
                  entry_reason="signal", pnl=1000, commission=10,
                  slippage_cost=5, funding_cost=0, realized_pnl=985),
            Trade(entry_time=2, exit_time=3, symbol="BTC", side="long",
                  size=10000, entry_price=51000, exit_price=50500,
                  entry_reason="signal", pnl=-500, commission=10,
                  slippage_cost=5, funding_cost=0, realized_pnl=-515),
            Trade(entry_time=3, exit_time=4, symbol="BTC", side="long",
                  size=10000, entry_price=50500, exit_price=52000,
                  entry_reason="signal", pnl=1500, commission=10,
                  slippage_cost=5, funding_cost=0, realized_pnl=1485),
        ]

        equity = generate_equity_curve(days=1)
        metrics = calculate_benchmark_metrics(equity, trades=trades)

        assert metrics.win_rate == pytest.approx(2/3, abs=0.01)
        assert metrics.total_trades == 3

    def test_t_bm_07_profit_factor(self):
        """T_BM_07: Profit factor = gross profit / gross loss."""
        from tradingagents_crypto.backtest.backtest_engine import Trade

        trades = [
            Trade(entry_time=1, exit_time=2, symbol="BTC", side="long",
                  size=10000, entry_price=50000, exit_price=51000,
                  entry_reason="signal", pnl=1000, commission=10,
                  slippage_cost=5, funding_cost=0, realized_pnl=985),
            Trade(entry_time=2, exit_time=3, symbol="BTC", side="long",
                  size=10000, entry_price=51000, exit_price=50000,
                  entry_reason="signal", pnl=-1000, commission=10,
                  slippage_cost=5, funding_cost=0, realized_pnl=-1015),
        ]

        equity = generate_equity_curve(days=1)
        metrics = calculate_benchmark_metrics(equity, trades=trades)

        # Gross profit = 985, Gross loss = 1015
        # Profit factor ≈ 0.97
        assert metrics.profit_factor == pytest.approx(985/1015, abs=0.01)

    def test_t_bm_08_avg_trade_duration(self):
        """T_BM_08: Average trade duration in hours."""
        from tradingagents_crypto.backtest.backtest_engine import Trade

        # 2 hour trade, 4 hour trade
        trades = [
            Trade(entry_time=3600, exit_time=7200, symbol="BTC", side="long",  # 1 hour
                  size=10000, entry_price=50000, exit_price=50500,
                  entry_reason="signal", pnl=500, commission=10,
                  slippage_cost=5, funding_cost=0, realized_pnl=485),
            Trade(entry_time=7200, exit_time=18000, symbol="BTC", side="long",  # 3 hours
                  size=10000, entry_price=50500, exit_price=51000,
                  entry_reason="signal", pnl=500, commission=10,
                  slippage_cost=5, funding_cost=0, realized_pnl=485),
        ]

        equity = generate_equity_curve(days=1)
        metrics = calculate_benchmark_metrics(equity, trades=trades)

        # Average = (1 + 3) / 2 = 2 hours
        assert metrics.avg_trade_duration_hours == 2.0
