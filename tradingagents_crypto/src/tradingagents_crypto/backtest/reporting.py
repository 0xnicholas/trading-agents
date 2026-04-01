"""
Backtest Reporting.

Generates markdown reports for backtest results.
"""
import logging
from datetime import datetime
from io import BytesIO
from typing import Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def generate_equity_curve_base64(equity_curve: pd.Series) -> str:
    """
    Generate equity curve as base64 encoded PNG.

    Args:
        equity_curve: Series with datetime index

    Returns:
        Base64 encoded string
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(equity_curve.index, equity_curve.values, linewidth=1.5)
    ax.set_xlabel("Date")
    ax.set_ylabel("Equity (USD)")
    ax.set_title("Equity Curve")
    ax.grid(True, alpha=0.3)

    # Format y-axis as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))

    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100)
    buf.seek(0)
    plt.close(fig)

    import base64
    return base64.b64encode(buf.read()).decode()


def generate_drawdown_curve_base64(equity_curve: pd.Series) -> str:
    """
    Generate drawdown curve as base64 encoded PNG.

    Args:
        equity_curve: Series with datetime index

    Returns:
        Base64 encoded string
    """
    equity_peak = equity_curve.cummax()
    drawdown = (equity_curve - equity_peak) / equity_peak

    fig, ax = plt.subplots(figsize=(12, 4))

    ax.fill_between(drawdown.index, drawdown.values, 0, alpha=0.3, color="red")
    ax.plot(drawdown.index, drawdown.values, linewidth=0.5, color="red")
    ax.set_xlabel("Date")
    ax.set_ylabel("Drawdown")
    ax.set_title("Drawdown Curve")
    ax.grid(True, alpha=0.3)

    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x:.0%}"))

    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100)
    buf.seek(0)
    plt.close(fig)

    import base64
    return base64.b64encode(buf.read()).decode()


def generate_monthly_returns_heatmap(equity_curve: pd.Series) -> Optional[str]:
    """
    Generate monthly returns heatmap as base64 PNG.

    Args:
        equity_curve: Series with datetime index

    Returns:
        Base64 encoded string or None if insufficient data
    """
    if len(equity_curve) < 60:  # Need at least ~2 months
        return None

    # Calculate monthly returns
    returns = equity_curve.resample("ME").last().pct_change().dropna()

    if len(returns) < 3:
        return None

    # Create DataFrame for heatmap
    returns_df = pd.DataFrame({
        "year": returns.index.year,
        "month": returns.index.month,
        "return": returns.values,
    })

    # Pivot
    pivot = returns_df.pivot(index="year", columns="month", values="return")

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto", vmin=-0.2, vmax=0.2)

    # Set ticks
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][:len(pivot.columns)])
    ax.set_yticklabels(pivot.index)

    # Colorbar
    plt.colorbar(im, ax=ax, label="Monthly Return")

    ax.set_title("Monthly Returns Heatmap")
    ax.set_xlabel("Month")
    ax.set_ylabel("Year")

    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100)
    buf.seek(0)
    plt.close(fig)

    import base64
    return base64.b64encode(buf.read()).decode()


def generate_markdown_report(
    result,
    strategy_name: str,
    output_path: Optional[str] = None,
    include_equity_chart: bool = True,
    include_drawdown_chart: bool = True,
    include_monthly_heatmap: bool = True,
) -> str:
    """
    Generate a markdown backtest report.

    Args:
        result: BacktestResult object
        strategy_name: Name of the strategy
        output_path: Optional path to save the report
        include_equity_chart: Include equity curve chart
        include_drawdown_chart: Include drawdown chart
        include_monthly_heatmap: Include monthly returns heatmap

    Returns:
        Markdown string
    """
    metrics = result.metrics
    confidence = result.confidence
    metadata = result.metadata

    # Generate charts
    equity_chart = None
    if include_equity_chart:
        try:
            equity_chart = generate_equity_curve_base64(result.equity_curve)
        except Exception as e:
            logger.warning(f"Failed to generate equity chart: {e}")

    drawdown_chart = None
    if include_drawdown_chart:
        try:
            drawdown_chart = generate_drawdown_curve_base64(result.equity_curve)
        except Exception as e:
            logger.warning(f"Failed to generate drawdown chart: {e}")

    monthly_chart = None
    if include_monthly_heatmap:
        try:
            monthly_chart = generate_monthly_returns_heatmap(result.equity_curve)
        except Exception as e:
            logger.warning(f"Failed to generate monthly heatmap: {e}")

    # Build markdown
    lines = [
        f"# Backtest Report: {strategy_name}",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Initial Capital | ${metadata.get('initial_capital', 0):,.2f} |",
        f"| Final Equity | ${metrics.equity_final:,.2f} |",
        f"| Total Return | {metrics.total_return:.2%} |",
        f"| Sharpe Ratio | {metrics.sharpe_ratio:.2f} |",
        f"| Max Drawdown | {metrics.max_drawdown:.2%} |",
        f"| Calmar Ratio | {metrics.calmar_ratio:.2f} |",
        f"| Win Rate | {metrics.win_rate:.1%} |",
        f"| Profit Factor | {metrics.profit_factor:.2f} |",
        f"| Total Trades | {metrics.total_trades} |",
        f"| Avg Trade Duration | {metrics.avg_trade_duration_hours:.1f} hours |",
        "",
        "## Charts",
        "",
    ]

    if equity_chart:
        lines.append(f"### Equity Curve")
        lines.append(f"![Equity Curve](data:image/png;base64,{equity_chart})")
        lines.append("")

    if drawdown_chart:
        lines.append(f"### Drawdown Curve")
        lines.append(f"![Drawdown Curve](data:image/png;base64,{drawdown_chart})")
        lines.append("")

    if monthly_chart:
        lines.append(f"### Monthly Returns")
        lines.append(f"![Monthly Returns](data:image/png;base64,{monthly_chart})")
        lines.append("")

    # Trade Log Summary
    if result.trades:
        lines.extend([
            "## Trade Log Summary",
            "",
            f"Total Trades: {len(result.trades)}",
            "",
            "| # | Entry Time | Exit Time | Side | Size | Entry Price | Exit Price | PnL |",
            "|---|------------|-----------|------|------|-------------|------------|-----|",
        ])

        for i, trade in enumerate(result.trades[:20]):  # First 20 trades
            entry_dt = datetime.fromtimestamp(trade.entry_time).strftime("%Y-%m-%d %H:%M")
            exit_dt = datetime.fromtimestamp(trade.exit_time).strftime("%Y-%m-%d %H:%M") if trade.exit_time else "Open"
            exit_price_str = f"${trade.exit_price:,.2f}" if trade.exit_price else "-"
            lines.append(
                f"| {i+1} | {entry_dt} | {exit_dt} | {trade.side} | ${trade.size:,.0f} | "
                f"${trade.entry_price:,.2f} | {exit_price_str} | "
                f"${trade.realized_pnl:,.2f} |"
            )

        if len(result.trades) > 20:
            lines.append(f"| ... | | | | | | | ({len(result.trades) - 20} more trades) |")

        lines.append("")

    # Confidence & Data Quality
    lines.extend([
        "## Data Quality & Confidence",
        "",
        f"| Aspect | Value |",
        f"|--------|-------|",
        f"| Data Completeness | {confidence.data_completeness:.1%} |",
        f"| Slippage Model | {confidence.slippage_model} |",
        f"| Funding History | {confidence.funding_history} |",
        f"| Leverage Effects | {confidence.leverage_effects} |",
        f"| Backtest Period | {metadata.get('start_date', 'N/A')} to {metadata.get('end_date', 'N/A')} |",
        f"| Bars Processed | {metadata.get('num_bars', 'N/A')} |",
        "",
        "### Confidence Notes",
        "",
        "- **Slippage Model**: `estimated` - Based on assumption model, not historical order book data",
        "- **Funding History**: `real` - Actual Hyperliquid funding rates used",
        "- **Leverage Effects**: `simplified` - Does not account for complex margin calculations",
        "",
    ])

    report = "\n".join(lines)

    # Save if path provided
    if output_path:
        with open(output_path, "w") as f:
            f.write(report)

    return report
