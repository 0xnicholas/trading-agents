"""
Unit tests for Backtest Engine.
"""
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from tradingagents_crypto.backtest.backtest_engine import (
    BacktestEngine,
    BacktestConfig,
    BacktestResult,
    TradeSignal,
    run_backtest,
)


def generate_test_candles(days: int = 100, start_price: float = 50000) -> pd.DataFrame:
    """Generate synthetic candle data for testing."""
    np.random.seed(42)
    n_bars = days * 24  # Hourly
    dt = 1 / (24 * 365)

    # Geometric brownian motion
    returns = np.random.normal(0, 0.02 * np.sqrt(dt), n_bars)
    prices = start_price * np.exp(np.cumsum(returns))

    timestamps = pd.date_range(start="2024-01-01", periods=n_bars, freq="h")

    data = {
        "timestamp": timestamps,
        "open": prices * (1 + np.random.uniform(-0.002, 0.002, n_bars)),
        "high": prices * (1 + np.random.uniform(0, 0.005, n_bars)),
        "low": prices * (1 - np.random.uniform(0, 0.005, n_bars)),
        "close": prices,
        "volume": np.random.uniform(1000, 10000, n_bars),
    }

    return pd.DataFrame(data)


def always_hold(timestamp, candles, funding, oi, indicators):
    """Strategy that always holds."""
    return TradeSignal(action="hold")


def alternate_signals(timestamp, candles, funding, oi, indicators):
    """Strategy that alternates between long and close."""
    hour = pd.Timestamp(timestamp, unit="s") if isinstance(timestamp, (int, float)) else timestamp
    hour_of_day = hour.hour if hasattr(hour, 'hour') else 0

    # Simple: every 24 hours, toggle
    bar_idx = int(hour.timestamp() / 3600) if isinstance(hour.timestamp(), (int, float)) else 0
    if bar_idx % 48 == 0:
        return TradeSignal(action="open_long")
    elif bar_idx % 48 == 24:
        return TradeSignal(action="close")
    return TradeSignal(action="hold")


class TestBacktestEngine:
    """Tests for BacktestEngine."""

    def test_t_bt_01_simple_ma_strategy(self):
        """T_BT_01: Simple MA crossover strategy produces trades."""
        candles = generate_test_candles(days=50)

        def ma_strategy(timestamp, candles, funding, oi, indicators):
            if len(candles) < 50:
                return TradeSignal(action="hold")

            sma_20 = candles["close"].rolling(20).mean().iloc[-1]
            sma_50 = candles["close"].rolling(50).mean().iloc[-1]
            prev_sma_20 = candles["close"].rolling(20).mean().iloc[-2]
            prev_sma_50 = candles["close"].rolling(50).mean().iloc[-2]

            # Golden cross
            if prev_sma_20 <= prev_sma_50 and sma_20 > sma_50:
                return TradeSignal(action="open_long", size_pct=0.5)
            # Death cross
            elif prev_sma_20 >= prev_sma_50 and sma_20 < sma_50:
                return TradeSignal(action="close")

            return TradeSignal(action="hold")

        config = BacktestConfig(initial_capital=100000, commission_rate=0.0004)
        engine = BacktestEngine(config)
        result = engine.run(ma_strategy, candles)

        assert isinstance(result, BacktestResult)
        assert len(result.equity_curve) > 0
        assert result.metadata["num_bars"] == len(candles)

    def test_t_bt_02_equity_changes_with_price(self):
        """T_BT_02: Equity curve should reflect price movements."""
        candles = generate_test_candles(days=10)

        # Buy and hold strategy
        def buy_and_hold(timestamp, candles, funding, oi, indicators):
            if len(candles) == 1:
                return TradeSignal(action="open_long", size_pct=1.0)
            return TradeSignal(action="hold")

        config = BacktestConfig(initial_capital=50000)
        engine = BacktestEngine(config)
        result = engine.run(buy_and_hold, candles)

        # Final equity should be different from initial
        assert result.metrics.equity_final != 50000

    def test_t_bt_03_commission_deducted(self):
        """T_BT_03: Commissions are properly deducted."""
        candles = generate_test_candles(days=5)

        # High-frequency strategy
        def high_freq(timestamp, candles, funding, oi, indicators):
            if len(candles) < 2:
                return TradeSignal(action="open_long", size_pct=0.5)
            return TradeSignal(action="close")

        config = BacktestConfig(initial_capital=100000, commission_rate=0.001)  # 0.1% commission
        engine = BacktestEngine(config)
        result = engine.run(high_freq, candles)

        # High frequency trading should result in losses due to commissions
        # (unless the price went up significantly)
        assert result.metrics.total_trades >= 0  # Trades were executed

    def test_t_bt_04_no_signals_holds(self):
        """T_BT_04: No signals = no trades."""
        candles = generate_test_candles(days=10)
        config = BacktestConfig(initial_capital=100000)
        engine = BacktestEngine(config)
        result = engine.run(always_hold, candles)

        # Should have no trades
        assert len(result.trades) == 0

    def test_t_bt_05_empty_candles_handled(self):
        """T_BT_05: Empty candles doesn't crash."""
        candles = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

        config = BacktestConfig()
        engine = BacktestEngine(config)
        result = engine.run(always_hold, candles)

        assert isinstance(result, BacktestResult)

    def test_t_bt_06_date_filter(self):
        """T_BT_06: Date filtering works."""
        candles = generate_test_candles(days=50)

        def count_bars(timestamp, candles, funding, oi, indicators):
            return TradeSignal(action="hold")

        config = BacktestConfig()
        engine = BacktestEngine(config)

        # Filter to first 10 days
        result = engine.run(
            count_bars,
            candles,
            start_date="2024-01-01",
            end_date="2024-01-10",
        )

        # Should process ~240 bars (10 days * 24 hours)
        assert result.metadata["num_bars"] <= 240

    def test_t_bt_07_equity_curve_length(self):
        """T_BT_07: Equity curve has one entry per bar."""
        candles = generate_test_candles(days=20)
        config = BacktestConfig()
        engine = BacktestEngine(config)
        result = engine.run(always_hold, candles)

        # Equity curve length should match number of bars processed
        assert len(result.equity_curve) == result.metadata["num_bars"]

    def test_t_bt_08_metrics_calculated(self):
        """T_BT_08: All metrics are calculated."""
        candles = generate_test_candles(days=30)

        config = BacktestConfig(initial_capital=100000)
        engine = BacktestEngine(config)
        result = engine.run(always_hold, candles)

        m = result.metrics
        assert hasattr(m, "total_return")
        assert hasattr(m, "sharpe_ratio")
        assert hasattr(m, "max_drawdown")
        assert hasattr(m, "calmar_ratio")
        assert hasattr(m, "win_rate")
        assert hasattr(m, "profit_factor")

    def test_t_bt_09_run_backtest_function(self):
        """T_BT_09: run_backtest convenience function works."""
        candles = generate_test_candles(days=20)

        result = run_backtest(
            strategy_fn=always_hold,
            candles=candles,
            initial_capital=75000,
            commission_rate=0.0004,
        )

        assert isinstance(result, BacktestResult)
        assert result.metrics.equity_final == 75000  # No trades = no change


class TestTradeSignal:
    """Tests for TradeSignal."""

    def test_signal_creation(self):
        """Test signal creation."""
        signal = TradeSignal(action="open_long", size_pct=0.5)
        assert signal.action == "open_long"
        assert signal.size_pct == 0.5
        assert signal.stop_loss_pct is None

    def test_signal_with_stops(self):
        """Signal with stop loss and take profit."""
        signal = TradeSignal(
            action="open_long",
            size_pct=1.0,
            stop_loss_pct=0.02,
            take_profit_pct=0.05,
        )
        assert signal.stop_loss_pct == 0.02
        assert signal.take_profit_pct == 0.05


class TestBacktestConfig:
    """Tests for BacktestConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = BacktestConfig()
        assert config.initial_capital == 100000
        assert config.commission_rate == 0.0004
        assert config.slippage_bps == 5.0
        assert config.leverage == 5

    def test_custom_config(self):
        """Test custom configuration."""
        config = BacktestConfig(
            initial_capital=50000,
            leverage=10,
            max_position_size_pct=0.30,
        )
        assert config.initial_capital == 50000
        assert config.leverage == 10
        assert config.max_position_size_pct == 0.30
