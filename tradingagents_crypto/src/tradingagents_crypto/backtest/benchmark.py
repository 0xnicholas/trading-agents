"""
Benchmark Comparators.

Compares backtest results against buy-and-hold benchmarks.
"""
import logging
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkMetrics:
    """Benchmark performance metrics."""
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float          # annual_return / |max_drawdown|
    win_rate: float
    profit_factor: float        # gross profit / gross loss
    avg_trade_duration_hours: float
    total_trades: int


def calculate_benchmark_metrics(
    equity_curve: pd.Series,
    trades: list = None,
) -> BenchmarkMetrics:
    """
    Calculate metrics for a benchmark equity curve.

    Args:
        equity_curve: Series with datetime index and equity values
        trades: Optional list of Trade objects

    Returns:
        BenchmarkMetrics
    """
    if len(equity_curve) < 2:
        return BenchmarkMetrics(
            total_return=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            calmar_ratio=0.0,
            win_rate=0.0,
            profit_factor=0.0,
            avg_trade_duration_hours=0.0,
            total_trades=0,
        )

    # Returns
    returns = equity_curve.pct_change().dropna()

    # Total return
    total_return = (equity_curve.iloc[-1] - equity_curve.iloc[0]) / equity_curve.iloc[0]

    # Max drawdown
    equity_peak = equity_curve.cummax()
    drawdown = (equity_curve - equity_peak) / equity_peak
    max_drawdown = drawdown.min()

    # Sharpe ratio (hourly data assumed)
    if len(returns) > 0 and returns.std() > 0:
        sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(365 * 24)
    else:
        sharpe_ratio = 0.0

    # Calmar ratio
    if abs(max_drawdown) > 0:
        calmar_ratio = total_return / abs(max_drawdown)
    else:
        calmar_ratio = 0.0

    # Trade metrics
    if trades:
        winning = [t for t in trades if t.realized_pnl > 0]
        losing = [t for t in trades if t.realized_pnl <= 0]
        win_rate = len(winning) / len(trades) if trades else 0.0

        gross_profit = sum(t.realized_pnl for t in winning)
        gross_loss = abs(sum(t.realized_pnl for t in losing))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

        durations = [t.exit_time - t.entry_time for t in trades if t.exit_time]
        avg_duration = np.mean(durations) / 3600 if durations else 0.0
    else:
        win_rate = 0.0
        profit_factor = 0.0
        avg_duration = 0.0

    return BenchmarkMetrics(
        total_return=total_return,
        sharpe_ratio=sharpe_ratio,
        max_drawdown=max_drawdown,
        calmar_ratio=calmar_ratio,
        win_rate=win_rate,
        profit_factor=profit_factor,
        avg_trade_duration_hours=avg_duration,
        total_trades=len(trades) if trades else 0,
    )


def compare_with_benchmark(
    backtest_result,
    benchmark_symbols: list[str] = None,
) -> dict[str, BenchmarkMetrics]:
    """
    Compare backtest result with buy-and-hold benchmarks.

    Args:
        backtest_result: BacktestResult object
        benchmark_symbols: List of symbols to compare against (e.g., ["BTC", "ETH"])

    Returns:
        Dict of symbol -> BenchmarkMetrics
    """
    results = {}

    # Compare with initial capital (no investment)
    # This represents "did nothing" baseline

    # In a real implementation, you would load price data for benchmark symbols
    # and calculate their equity curves. For now, return empty results.

    return results


def print_metrics_comparison(
    strategy_metrics,
    benchmark_metrics: BenchmarkMetrics,
    strategy_name: str = "Strategy",
    benchmark_name: str = "Buy & Hold",
) -> None:
    """
    Print a formatted comparison of metrics.

    Args:
        strategy_metrics: Metrics from backtest result
        benchmark_metrics: BenchmarkMetrics object
        strategy_name: Name for strategy column
        benchmark_name: Name for benchmark column
    """
    print(f"\n{'='*60}")
    print(f"Performance Comparison: {strategy_name} vs {benchmark_name}")
    print(f"{'='*60}")
    print(f"{'Metric':<20} {strategy_name:>18} {benchmark_name:>18}")
    print(f"{'-'*60}")
    print(f"{'Total Return':<20} {strategy_metrics.total_return:>17.2%} {benchmark_metrics.total_return:>17.2%}")
    print(f"{'Sharpe Ratio':<20} {strategy_metrics.sharpe_ratio:>18.2f} {benchmark_metrics.sharpe_ratio:>18.2f}")
    print(f"{'Max Drawdown':<20} {strategy_metrics.max_drawdown:>17.2%} {benchmark_metrics.max_drawdown:>17.2%}")
    print(f"{'Calmar Ratio':<20} {strategy_metrics.calmar_ratio:>18.2f} {benchmark_metrics.calmar_ratio:>18.2f}")
    print(f"{'Win Rate':<20} {strategy_metrics.win_rate:>17.1%} {benchmark_metrics.win_rate:>17.1%}")
    print(f"{'Profit Factor':<20} {strategy_metrics.profit_factor:>18.2f} {benchmark_metrics.profit_factor:>18.2f}")
    print(f"{'Total Trades':<20} {strategy_metrics.total_trades:>18d} {benchmark_metrics.total_trades:>18d}")
    print(f"{'='*60}\n")
