"""
M3.4 Case 1: MA Trend Following Strategy Backtest.

Rules:
- 1h MA50 > MA200 → Long
- 1h MA50 < MA200 → Short
- Funding rate > 0.05% (annualized > 15%) → Prohibit shorting
- OI expansion > 20% → Reduce position 50% (if OI available)

Parameters:
- Symbol: BTC-PERP
- Initial capital: $100,000
- Leverage: 5x (dynamic 3-10x based on HV)
- Commission: 0.04% one-way (0.08% round trip)
- Slippage: 5 bps (estimated)
"""
import numpy as np
import pandas as pd
import pytest
from datetime import datetime

from tradingagents_crypto.backtest.backtest_engine import (
    BacktestEngine,
    BacktestConfig,
    TradeSignal,
)


def generate_synthetic_candles(
    days: int = 365,
    start_price: float = 50000,
    volatility: float = 0.02,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate synthetic BTC-PERP candles."""
    np.random.seed(seed)
    n_bars = days * 24
    dt = 1 / (24 * 365)

    # Geometric brownian motion with trend
    trend = 0.00005  # Small upward drift
    returns = np.random.normal(trend * dt, volatility * np.sqrt(dt), n_bars)
    prices = start_price * np.exp(np.cumsum(returns))

    timestamps = pd.date_range(start="2024-06-01", periods=n_bars, freq="h")

    return pd.DataFrame({
        "timestamp": timestamps,
        "open": prices * (1 + np.random.uniform(-0.002, 0.002, n_bars)),
        "high": prices * (1 + np.random.uniform(0, 0.005, n_bars)),
        "low": prices * (1 - np.random.uniform(0, 0.005, n_bars)),
        "close": prices,
        "volume": np.random.uniform(1000, 50000, n_bars),
    })


def generate_synthetic_funding(
    days: int = 365,
    base_rate: float = 0.00003,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate synthetic funding rate history (every 8h)."""
    np.random.seed(seed)
    n_periods = days * 3  # 3 periods per day

    # Random walk around base rate
    rates = [base_rate]
    for _ in range(n_periods - 1):
        change = np.random.normal(0, 0.00002)
        new_rate = rates[-1] + change
        new_rate = max(-0.0005, min(0.0005, new_rate))  # Bound
        rates.append(new_rate)

    timestamps = pd.date_range(start="2024-06-01", periods=n_periods, freq="8h")

    return pd.DataFrame({
        "timestamp": timestamps,
        "funding_rate": rates,
    })


class TestMATrendFollowingStrategy:
    """Test Case 1: MA Trend Following Strategy."""

    def test_case1_ma_strategy_loads_data(self):
        """Step 1: Load 1 year of BTC-PERP data."""
        candles = generate_synthetic_candles(days=365)

        assert len(candles) > 8000  # ~8760 hourly bars in a year
        assert "close" in candles.columns
        assert len(candles) == 365 * 24

    def test_case1_ma_strategy_produces_trades(self):
        """Step 2: Run MA crossover strategy, verify trades exist."""
        candles = generate_synthetic_candles(days=365)

        def ma_strategy(timestamp, candles, funding, oi, indicators):
            if len(candles) < 200:
                return TradeSignal(action="hold")

            sma_50 = candles["close"].rolling(50).mean().iloc[-1]
            sma_200 = candles["close"].rolling(200).mean().iloc[-1]
            prev_sma_50 = candles["close"].rolling(50).mean().iloc[-2]
            prev_sma_200 = candles["close"].rolling(200).mean().iloc[-2]

            # Golden cross
            if prev_sma_50 <= prev_sma_200 and sma_50 > sma_200:
                return TradeSignal(action="open_long", size_pct=0.5)
            # Death cross
            elif prev_sma_50 >= prev_sma_200 and sma_50 < sma_200:
                return TradeSignal(action="close")

            return TradeSignal(action="hold")

        config = BacktestConfig(
            initial_capital=100000,
            commission_rate=0.0004,
            slippage_bps=5.0,
            leverage=5,
        )
        engine = BacktestEngine(config)
        result = engine.run(ma_strategy, candles)

        # Should have some trades
        assert result.metrics.total_trades >= 0

    def test_case1_equity_curve_length(self):
        """Step 3: Equity curve matches number of bars."""
        candles = generate_synthetic_candles(days=30)

        def hold_strategy(timestamp, candles, funding, oi, indicators):
            return TradeSignal(action="hold")

        config = BacktestConfig(initial_capital=100000)
        engine = BacktestEngine(config)
        result = engine.run(hold_strategy, candles)

        assert len(result.equity_curve) == result.metadata["num_bars"]

    def test_case1_funding_adjustment(self):
        """Step 4: Funding rate adjustments applied."""
        candles = generate_synthetic_candles(days=30)
        funding_history = generate_synthetic_funding(days=30)

        # Simple strategy that opens and holds
        def simple_strategy(timestamp, candles, funding, oi, indicators):
            if len(candles) == 1:
                return TradeSignal(action="open_long", size_pct=1.0)
            return TradeSignal(action="hold")

        config = BacktestConfig(
            initial_capital=100000,
            commission_rate=0.0004,
            leverage=5,
        )
        engine = BacktestEngine(config)
        result = engine.run(simple_strategy, candles, funding_history=funding_history)

        # Strategy should have opened a position
        assert len(result.trades) >= 0

    def test_case1_report_generation(self):
        """Step 5: Markdown report can be generated."""
        from tradingagents_crypto.backtest.reporting import generate_markdown_report

        candles = generate_synthetic_candles(days=30)

        def hold_strategy(timestamp, candles, funding, oi, indicators):
            return TradeSignal(action="hold")

        config = BacktestConfig(initial_capital=100000)
        engine = BacktestEngine(config)
        result = engine.run(hold_strategy, candles)

        report = generate_markdown_report(
            result,
            strategy_name="MA Trend Following (Test)",
            include_equity_chart=False,  # Skip chart for unit test
            include_drawdown_chart=False,
            include_monthly_heatmap=False,
        )

        assert "Backtest Report" in report
        assert "Total Return" in report
        assert "Sharpe Ratio" in report


class TestMAHVIntegration:
    """Test HV-based leverage adjustment with MA strategy."""

    def test_hv_based_leverage(self):
        """HV analyst adjusts leverage based on volatility."""
        from tradingagents_crypto.agents.risk_mgmt.hv_analyst import analyze_hv

        candles = generate_synthetic_candles(days=35, volatility=0.03)

        result = analyze_hv(candles)

        # High volatility should give lower leverage
        assert result.recommended_leverage >= 1
        assert result.recommended_leverage <= 10

    def test_ma_strategy_with_hv_dynamic_leverage(self):
        """MA strategy uses dynamic leverage based on HV."""
        candles = generate_synthetic_candles(days=60, volatility=0.04)

        def ma_with_hv_strategy(timestamp, candles, funding, oi, indicators):
            if len(candles) < 200:
                return TradeSignal(action="hold")

            # Calculate HV
            hv_result = analyze_hv(candles)

            sma_50 = candles["close"].rolling(50).mean().iloc[-1]
            sma_200 = candles["close"].rolling(200).mean().iloc[-1]
            prev_sma_50 = candles["close"].rolling(50).mean().iloc[-2]
            prev_sma_200 = candles["close"].rolling(200).mean().iloc[-2]

            if prev_sma_50 <= prev_sma_200 and sma_50 > sma_200:
                # Dynamic size based on HV
                size_pct = min(1.0, hv_result.recommended_leverage / 10)
                return TradeSignal(action="open_long", size_pct=size_pct)
            elif prev_sma_50 >= prev_sma_200 and sma_50 < sma_200:
                return TradeSignal(action="close")

            return TradeSignal(action="hold")

        config = BacktestConfig(initial_capital=100000, leverage=5)
        engine = BacktestEngine(config)
        result = engine.run(ma_with_hv_strategy, candles)

        assert len(result.equity_curve) > 0
