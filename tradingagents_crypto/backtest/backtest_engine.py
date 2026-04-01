"""
Backtest Engine.

A rule-based backtesting engine for crypto perpetual strategies.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Literal, Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TradeSignal:
    """A trading signal from a strategy function."""
    action: Literal["open_long", "open_short", "close", "reduce", "hold"]
    size_pct: float = 1.0       # Position size as % of available capital (0.0-1.0)
    stop_loss_pct: float | None = None   # Stop loss % (e.g., 0.02 = 2%)
    take_profit_pct: float | None = None  # Take profit % (e.g., 0.05 = 5%)


@dataclass
class Trade:
    """A completed trade."""
    entry_time: int
    exit_time: int | None
    symbol: str
    side: Literal["long", "short"]
    size: float           # Size in USD
    entry_price: float
    exit_price: float | None
    entry_reason: str     # e.g., "signal", "stop_loss", "take_profit"
    pnl: float = 0.0
    commission: float = 0.0
    slippage_cost: float = 0.0
    funding_cost: float = 0.0
    realized_pnl: float = 0.0


@dataclass
class BacktestConfidence:
    """Confidence level of backtest results."""
    data_completeness: float = 1.0  # 0.0-1.0
    slippage_model: str = "estimated"
    funding_history: str = "real"
    leverage_effects: str = "simplified"


@dataclass
class BacktestMetrics:
    """Performance metrics."""
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float
    win_rate: float
    profit_factor: float
    avg_trade_duration_hours: float
    total_trades: int
    equity_final: float
    equity_peak: float


@dataclass
class BacktestResult:
    """Complete backtest result."""
    equity_curve: pd.Series     # DatetimeIndex -> equity value
    trades: list[Trade]
    metrics: BacktestMetrics
    confidence: BacktestConfidence
    metadata: dict


@dataclass
class BacktestConfig:
    """Backtest configuration."""
    initial_capital: float = 100_000.0
    commission_rate: float = 0.0004   # Per side (0.04% HL taker fee)
    slippage_bps: float = 5.0         # Estimated slippage in bps
    leverage: int = 5
    max_position_size_pct: float = 0.20  # Max 20% of equity per position
    funding_rate: float = 0.0001      # Default 8h funding rate
    default_symbol: str = "BTC"        # Default symbol for single-asset backtest


@dataclass
class BacktestPosition:
    """Internal position representation during backtest."""
    symbol: str
    side: Literal["long", "short"]
    size: float           # In units
    entry_price: float
    current_price: float
    leverage: int
    margin_usd: float
    entry_time: int
    unrealized_pnl: float = 0.0
    entry_reason: str = "signal"
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None

    @property
    def notional_value(self) -> float:
        """Notional value of the position."""
        return self.size * self.current_price

    @property
    def notional_value_usd(self) -> float:
        """Notional value in USD terms."""
        return self.size * self.current_price


class BacktestEngine:
    """
    Rule-based backtest engine for crypto perpetuals.

    Supports multi-position backtesting with multiple symbols.
    Slippage is incorporated into execution price, not deducted separately.

    Usage:
        def my_strategy(timestamp, candles, funding, oi, indicators):
            # Return TradeSignal
            return TradeSignal(action="open_long", size_pct=0.5)

        engine = BacktestEngine(config=BacktestConfig())
        result = engine.run(
            strategy_fn=my_strategy,
            candles=candles_df,
            funding_history=funding_df,
        )
    """

    def __init__(self, config: Optional[BacktestConfig] = None):
        self.config = config or BacktestConfig()

        # State - supports multiple positions
        self._equity = 0.0
        self._cash = 0.0
        self._positions: dict[str, BacktestPosition] = {}  # symbol -> position
        self._equity_curve = []
        self._trades = []
        self._indicators_cache = {}
        self._last_funding_time = None

    def run(
        self,
        strategy_fn: Callable,
        candles: pd.DataFrame,
        funding_history: Optional[pd.DataFrame] = None,
        oi_history: Optional[pd.DataFrame] = None,
        oi_available: bool = True,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> BacktestResult:
        """
        Run backtest.

        Args:
            strategy_fn: Strategy function(timestamp, candles, funding, oi, indicators) -> TradeSignal
            candles: DataFrame with columns [timestamp, open, high, low, close, volume]
            funding_history: Optional DataFrame with [timestamp, funding_rate]
            oi_history: Optional DataFrame with [timestamp, open_interest]
            oi_available: Whether OI data is available
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            BacktestResult with equity curve, trades, and metrics
        """
        # Initialize
        self._equity = self.config.initial_capital
        self._cash = self.config.initial_capital
        self._positions = {}
        self._equity_curve = []
        self._trades = []
        self._indicators_cache = {}
        self._last_funding_time = None

        # Filter by date if specified
        if start_date:
            candles = candles[candles["timestamp"] >= pd.to_datetime(start_date)]
        if end_date:
            candles = candles[candles["timestamp"] <= pd.to_datetime(end_date)]

        # Create funding lookup
        funding_lookup = {}
        if funding_history is not None and len(funding_history) > 0:
            funding_lookup = funding_history.set_index("timestamp")["funding_rate"].to_dict()

        # Create OI lookup
        oi_lookup = {}
        if oi_history is not None and len(oi_history) > 0 and oi_available:
            oi_lookup = oi_history.set_index("timestamp")["open_interest"].to_dict()

        # Pre-calculate indicators
        self._indicators_cache = self._calculate_indicators(candles)

        # Main backtest loop - use integer index for efficiency
        candle_indices = candles.index.tolist()
        for i, idx in enumerate(candle_indices):
            row = candles.loc[idx]
            ts = row["timestamp"]
            current_price = row["close"]

            # Update equity based on current positions
            self._update_equity(current_price, ts)

            # Get funding rate for this timestamp
            funding = funding_lookup.get(ts, self.config.funding_rate)

            # Apply funding cost to all open positions
            if self._last_funding_time is not None:
                hours_elapsed = (ts - self._last_funding_time).total_seconds() / 3600
                if hours_elapsed >= 8:  # Funding settles every 8h
                    self._apply_funding_cost(funding, hours_elapsed)
                    self._last_funding_time = ts
            else:
                self._last_funding_time = ts

            # Get OI
            oi = oi_lookup.get(ts, None) if oi_available else None

            # Get indicators for this timestamp
            indicators = self._get_indicators_at(idx, candles)

            # Get strategy signal - pass slice using iloc (efficient, no copy)
            try:
                signal = strategy_fn(
                    timestamp=int(ts.timestamp()),
                    candles=candles.iloc[:i+1],  # Efficient slice, no copy
                    funding=funding,
                    oi=oi,
                    indicators=indicators,
                )
            except Exception as e:
                logger.warning(f"Strategy function error at {ts}: {e}")
                signal = TradeSignal(action="hold")

            if signal is None:
                signal = TradeSignal(action="hold")

            # Process signal
            self._process_signal(signal, current_price, ts, funding)

            # Record equity
            total_position_value = sum(p.notional_value_usd for p in self._positions.values())
            self._equity_curve.append({
                "timestamp": ts,
                "equity": self._equity,
                "position_value": total_position_value,
            })

        # Close all open positions at final price
        for symbol in list(self._positions.keys()):
            final_price = candles.iloc[-1]["close"]
            self._close_position(symbol, final_price, candles.iloc[-1]["timestamp"], "end_of_backtest")

        # Calculate metrics
        if self._equity_curve:
            equity_df = pd.DataFrame(self._equity_curve).set_index("timestamp")
            metrics = self._calculate_metrics(equity_df)
        else:
            equity_df = pd.DataFrame(columns=["equity"])
            metrics = self._calculate_metrics(equity_df)
        confidence = self._estimate_confidence(candles)

        return BacktestResult(
            equity_curve=equity_df["equity"],
            trades=self._trades,
            metrics=metrics,
            confidence=confidence,
            metadata={
                "initial_capital": self.config.initial_capital,
                "start_date": str(candles.iloc[0]["timestamp"]) if len(candles) > 0 else None,
                "end_date": str(candles.iloc[-1]["timestamp"]) if len(candles) > 0 else None,
                "num_bars": len(candles) if len(candles) > 0 else 0,
            },
        )

    def _calculate_indicators(self, candles: pd.DataFrame) -> dict:
        """Pre-calculate indicators from candles."""
        indicators = {}

        if len(candles) < 50:
            return indicators

        close = candles["close"]

        # Simple Moving Averages
        indicators["sma_20"] = close.rolling(20).mean()
        indicators["sma_50"] = close.rolling(50).mean()
        indicators["sma_200"] = close.rolling(200).mean()

        # Exponential Moving Averages
        indicators["ema_12"] = close.ewm(span=12).mean()
        indicators["ema_26"] = close.ewm(span=26).mean()

        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.inf)
        indicators["rsi_14"] = 100 - (100 / (1 + rs))

        # MACD
        indicators["macd"] = indicators["ema_12"] - indicators["ema_26"]
        indicators["macd_signal"] = indicators["macd"].ewm(span=9).mean()

        # Bollinger Bands
        sma20 = indicators["sma_20"]
        std20 = close.rolling(20).std()
        indicators["bb_upper"] = sma20 + (std20 * 2)
        indicators["bb_lower"] = sma20 - (std20 * 2)

        # Returns
        indicators["returns"] = close.pct_change()

        return indicators

    def _get_indicators_at(self, idx, candles: pd.DataFrame) -> dict:
        """Get indicators at a specific index."""
        result = {}
        for name, series in self._indicators_cache.items():
            if idx in series.index:
                result[name] = series.loc[idx]
            else:
                result[name] = np.nan
        return result

    def _update_equity(self, current_price: float, timestamp: pd.Timestamp) -> None:
        """Update equity based on all open positions."""
        total_unrealized = 0.0
        for pos in self._positions.values():
            pos.current_price = current_price
            if pos.side == "long":
                unrealized = (current_price - pos.entry_price) * pos.size
            else:
                unrealized = (pos.entry_price - current_price) * pos.size
            pos.unrealized_pnl = unrealized
            total_unrealized += unrealized

        self._equity = self._cash + total_unrealized

    def _apply_funding_cost(self, funding_rate: float, hours_elapsed: float) -> None:
        """Apply funding cost to all open positions."""
        for pos in self._positions.values():
            position_value = pos.notional_value_usd
            if pos.side == "long":
                # Longs pay when rate is positive
                cost = -funding_rate * position_value
            else:
                # Shorts receive when rate is positive
                cost = funding_rate * position_value

            # Scale by time elapsed (assuming 8h periods)
            periods = hours_elapsed / 8.0
            total_cost = cost * periods

            self._cash += total_cost

    def _process_signal(
        self,
        signal: TradeSignal,
        current_price: float,
        timestamp: pd.Timestamp,
        funding: float,
    ) -> None:
        """Process a trading signal."""
        if signal.action == "hold":
            return

        symbol = self.config.default_symbol

        if signal.action == "open_long":
            if symbol in self._positions:
                self._close_position(symbol, current_price, timestamp, "reversal")
            self._open_position(symbol, "long", current_price, timestamp, signal.size_pct)

        elif signal.action == "open_short":
            if symbol in self._positions:
                self._close_position(symbol, current_price, timestamp, "reversal")
            self._open_position(symbol, "short", current_price, timestamp, signal.size_pct)

        elif signal.action == "close":
            if symbol in self._positions:
                self._close_position(symbol, current_price, timestamp, "signal")

        elif signal.action == "reduce":
            if symbol in self._positions:
                self._close_position(symbol, current_price, timestamp, "reduce")

    def _open_position(
        self,
        symbol: str,
        side: Literal["long", "short"],
        price: float,
        timestamp: pd.Timestamp,
        size_pct: float,
    ) -> None:
        """Open a new position with slippage incorporated into execution price."""
        # Calculate position size
        max_size = self._equity * self.config.max_position_size_pct
        size_usd = self._equity * size_pct * self.config.leverage
        size_usd = min(size_usd, max_size)

        if size_usd <= 0:
            return

        # Calculate margin required
        margin_required = size_usd / self.config.leverage

        # Slippage: incorporate into execution price (not deducted separately)
        slippage_bps = self.config.slippage_bps
        if side == "long":
            # Longs pay higher price
            execution_price = price * (1 + slippage_bps / 10000)
        else:
            # Shorts receive lower price
            execution_price = price * (1 - slippage_bps / 10000)

        # Commission (deducted from cash)
        commission = size_usd * self.config.commission_rate

        # Deduct margin + commission from cash
        self._cash -= (margin_required + commission)

        # Create position
        size_units = size_usd / execution_price
        self._positions[symbol] = BacktestPosition(
            symbol=symbol,
            side=side,
            size=size_units,
            entry_price=execution_price,
            current_price=execution_price,
            leverage=self.config.leverage,
            margin_usd=margin_required,
            entry_time=int(timestamp.timestamp()),
            unrealized_pnl=0.0,
            entry_reason="signal",
            stop_loss_pct=None,
            take_profit_pct=None,
        )

        logger.debug(f"Opened {side} {symbol}: {size_units} @ {execution_price}")

    def _close_position(
        self,
        symbol: str,
        price: float,
        timestamp: pd.Timestamp,
        reason: str,
    ) -> None:
        """Close a position with slippage incorporated into execution price."""
        if symbol not in self._positions:
            return

        pos = self._positions[symbol]

        # Slippage: incorporate into execution price
        slippage_bps = self.config.slippage_bps
        if pos.side == "long":
            # Longs sell at lower price
            execution_price = price * (1 - slippage_bps / 10000)
        else:
            # Shorts buy at higher price
            execution_price = price * (1 + slippage_bps / 10000)

        # Calculate PnL at execution price
        if pos.side == "long":
            pnl = (execution_price - pos.entry_price) * pos.size
        else:
            pnl = (pos.entry_price - execution_price) * pos.size

        # Commission on exit
        size_usd = pos.size * execution_price
        commission = size_usd * self.config.commission_rate

        # Realized PnL after commission
        realized_pnl = pnl - commission

        # Update cash: return margin + realized PnL
        self._cash += pos.margin_usd + realized_pnl

        # Create trade record
        trade = Trade(
            entry_time=pos.entry_time,
            exit_time=int(timestamp.timestamp()),
            symbol=pos.symbol,
            side=pos.side,
            size=size_usd,
            entry_price=pos.entry_price,
            exit_price=execution_price,
            entry_reason=pos.entry_reason,
            pnl=pnl,
            commission=commission,
            slippage_cost=abs(price - execution_price) * pos.size,  # Slippage cost in price terms
            funding_cost=0.0,
            realized_pnl=realized_pnl,
        )
        self._trades.append(trade)

        logger.debug(f"Closed {pos.side} {symbol}: {reason}, PnL={realized_pnl:.2f}")

        del self._positions[symbol]

    def _calculate_metrics(self, equity_df: pd.DataFrame) -> BacktestMetrics:
        """Calculate performance metrics."""
        equity = equity_df["equity"]

        # Basic metrics
        total_return = (equity.iloc[-1] - equity.iloc[0]) / equity.iloc[0] if len(equity) > 1 else 0.0
        equity_peak = equity.cummax()
        drawdown = (equity - equity_peak) / equity_peak
        max_drawdown = drawdown.min() if len(drawdown) > 0 else 0.0

        # Sharpe ratio
        returns = equity.pct_change().dropna()
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
        if len(self._trades) > 0:
            winning_trades = [t for t in self._trades if t.realized_pnl > 0]
            losing_trades = [t for t in self._trades if t.realized_pnl <= 0]
            win_rate = len(winning_trades) / len(self._trades)

            total_wins = sum(t.realized_pnl for t in winning_trades)
            total_losses = abs(sum(t.realized_pnl for t in losing_trades))
            profit_factor = total_wins / total_losses if total_losses > 0 else 0.0

            durations = [t.exit_time - t.entry_time for t in self._trades if t.exit_time]
            avg_duration = np.mean(durations) / 3600 if durations else 0.0
        else:
            win_rate = 0.0
            profit_factor = 0.0
            avg_duration = 0.0

        return BacktestMetrics(
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_trade_duration_hours=avg_duration,
            total_trades=len(self._trades),
            equity_final=equity.iloc[-1] if len(equity) > 0 else self.config.initial_capital,
            equity_peak=equity_peak.max() if len(equity_peak) > 0 else self.config.initial_capital,
        )

    def _estimate_confidence(self, candles: pd.DataFrame) -> BacktestConfidence:
        """Estimate confidence level of results."""
        expected_bars = len(candles)
        actual_gaps = 0

        if expected_bars > 1:
            time_diffs = candles["timestamp"].diff().dt.total_seconds()
            expected_diff = 3600
            large_gaps = time_diffs[time_diffs > expected_diff * 2]
            actual_gaps = len(large_gaps)

        completeness = max(0.0, 1.0 - (actual_gaps / expected_bars)) if expected_bars > 0 else 1.0

        return BacktestConfidence(
            data_completeness=completeness,
            slippage_model="estimated",
            funding_history="real" if completeness > 0.95 else "partial",
            leverage_effects="simplified",
        )


def run_backtest(
    strategy_fn: Callable,
    candles: pd.DataFrame,
    funding_history: Optional[pd.DataFrame] = None,
    **kwargs,
) -> BacktestResult:
    """
    Convenience function to run a backtest.

    Args:
        strategy_fn: Strategy function
        candles: DataFrame with OHLCV data
        funding_history: Optional funding rate history
        **kwargs: Additional config options

    Returns:
        BacktestResult
    """
    config = BacktestConfig(**kwargs)
    engine = BacktestEngine(config)
    return engine.run(strategy_fn, candles, funding_history)
