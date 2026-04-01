"""Backtest package."""

from tradingagents_crypto.backtest.backtest_engine import (
    BacktestEngine,
    BacktestConfig,
    BacktestResult,
    BacktestMetrics,
    BacktestConfidence,
    TradeSignal,
    run_backtest,
)
from tradingagents_crypto.backtest.funding_simulator import (
    calc_funding_pnl,
    calc_funding_cost,
    annualize_funding_rate,
    format_funding_rate,
)
from tradingagents_crypto.backtest.slippage_estimator import (
    estimate_slippage,
    estimate_slippage_simple,
    calculate_execution_price,
)
from tradingagents_crypto.backtest.benchmark import (
    calculate_benchmark_metrics,
    BenchmarkMetrics,
    compare_with_benchmark,
    print_metrics_comparison,
)
from tradingagents_crypto.backtest.reporting import (
    generate_markdown_report,
    generate_equity_curve_base64,
    generate_drawdown_curve_base64,
)
from tradingagents_crypto.backtest.data_cache import (
    BacktestDataCache,
    GapCheckResult,
    DataGap,
)

__all__ = [
    # Engine
    "BacktestEngine",
    "BacktestConfig",
    "BacktestResult",
    "BacktestMetrics",
    "BacktestConfidence",
    "TradeSignal",
    "run_backtest",
    # Funding
    "calc_funding_pnl",
    "calc_funding_cost",
    "annualize_funding_rate",
    "format_funding_rate",
    # Slippage
    "estimate_slippage",
    "estimate_slippage_simple",
    "calculate_execution_price",
    # Benchmark
    "calculate_benchmark_metrics",
    "BenchmarkMetrics",
    "compare_with_benchmark",
    "print_metrics_comparison",
    # Reporting
    "generate_markdown_report",
    "generate_equity_curve_base64",
    "generate_drawdown_curve_base64",
    # Data Cache
    "BacktestDataCache",
    "GapCheckResult",
    "DataGap",
]
