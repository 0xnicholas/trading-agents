"""
Crypto Portfolio Manager.

Manages multi-asset crypto perpetual positions with leverage support.
"""
import logging
from dataclasses import dataclass, field
from typing import Literal, Optional

from tradingagents_crypto.agents.risk_mgmt.exposure_monitor import (
    Position,
    ExposureCheckResult,
    ExposureViolation,
    check_exposure,
    MAX_SINGLE_ASSET_EXPOSURE,
)

logger = logging.getLogger(__name__)


@dataclass
class CryptoPosition:
    """A crypto perpetual position."""
    symbol: str
    side: Literal["long", "short"]
    size: float              # Contract size (in units, not USD)
    entry_price: float
    mark_price: float
    leverage: int
    margin_usd: float       # Margin in USD
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0

    @property
    def notional_value(self) -> float:
        """Notional value of the position."""
        return self.size * self.mark_price

    def update_mark_price(self, new_mark_price: float) -> None:
        """Update mark price and recalculate unrealized PnL."""
        if self.side == "long":
            self.unrealized_pnl = (new_mark_price - self.entry_price) * self.size
        else:
            self.unrealized_pnl = (self.entry_price - new_mark_price) * self.size
        self.mark_price = new_mark_price


@dataclass
class CryptoPortfolioManager:
    """
    Crypto portfolio manager for perpetual futures.

    Manages multi-asset positions with:
    - Long/short support
    - Margin tracking
    - Liquidation monitoring
    - Exposure limits

    Usage:
        from agents.managers import create_portfolio_manager
        config = {"mode": "crypto", "max_leverage": 20}
        pm = create_portfolio_manager(config)
    """

    def __init__(self, config: Optional[dict] = None):
        """Initialize with optional config."""
        self.config = config or {}
        self.max_leverage = self.config.get("max_leverage", 20)
        self.positions: dict[str, CryptoPosition] = {}  # symbol -> position
        self._total_equity = self.config.get("initial_equity", 100_000.0)
        self._realized_pnl = 0.0

    @property
    def total_equity(self) -> float:
        """Calculate total equity from all positions."""
        total = self._total_equity + self._realized_pnl
        for pos in self.positions.values():
            total += pos.unrealized_pnl
        return total

    @property
    def total_unrealized_pnl(self) -> float:
        """Sum of all unrealized PnLs."""
        return sum(pos.unrealized_pnl for pos in self.positions.values())

    @property
    def total_realized_pnl(self) -> float:
        """Sum of all realized PnLs."""
        return self._realized_pnl + sum(pos.realized_pnl for pos in self.positions.values())

    def add_position(
        self,
        symbol: str,
        side: Literal["long", "short"],
        size: float,
        entry_price: float,
        leverage: int,
    ) -> ExposureCheckResult:
        """
        Add a new position.

        Args:
            symbol: Trading pair symbol (e.g., "BTC")
            side: "long" or "short"
            size: Contract size
            entry_price: Entry price
            leverage: Leverage level

        Returns:
            ExposureCheckResult indicating if position was approved
        """
        # Create position object for exposure check
        mark_price = entry_price  # Use entry as initial mark
        notional_value = size * mark_price
        margin_usd = notional_value / leverage

        new_pos = Position(
            symbol=symbol,
            side=side,
            size_usd=notional_value,
            entry_price=entry_price,
            current_price=mark_price,
            leverage=leverage,
        )

        # Check exposure
        existing_positions = self._to_exposure_positions()
        result = check_exposure(existing_positions, self.total_equity, new_pos)

        if not result.approved:
            logger.warning(f"Position rejected: {[v.detail for v in result.violations]}")
            return result

        # Create actual position
        crypto_pos = CryptoPosition(
            symbol=symbol,
            side=side,
            size=size,
            entry_price=entry_price,
            mark_price=mark_price,
            leverage=leverage,
            margin_usd=margin_usd,
        )

        self.positions[symbol] = crypto_pos
        logger.info(f"Position added: {side} {size} {symbol} @ {entry_price}, lev={leverage}x")

        return result

    def remove_position(self, symbol: str, exit_price: float) -> Optional[CryptoPosition]:
        """
        Close and remove a position.

        Args:
            symbol: Symbol to close
            exit_price: Exit market price

        Returns:
            Closed position or None if not found
        """
        if symbol not in self.positions:
            logger.warning(f"Position not found: {symbol}")
            return None

        pos = self.positions[symbol]

        # Calculate final PnL
        if pos.side == "long":
            pnl = (exit_price - pos.entry_price) * pos.size
        else:
            pnl = (pos.entry_price - exit_price) * pos.size

        pos.realized_pnl = pnl
        pos.unrealized_pnl = 0.0
        self._realized_pnl += pnl

        # Remove position
        closed_pos = self.positions.pop(symbol)
        logger.info(f"Position closed: {symbol} @ {exit_price}, PnL={pnl:.2f}")

        return closed_pos

    def update_mark_prices(self, prices: dict[str, float]) -> None:
        """
        Update mark prices for all positions.

        Args:
            prices: Dict of symbol -> mark_price
        """
        for symbol, mark_price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].update_mark_price(mark_price)

    def get_position(self, symbol: str) -> Optional[CryptoPosition]:
        """Get position by symbol."""
        return self.positions.get(symbol)

    def get_all_positions(self) -> list[CryptoPosition]:
        """Get all open positions."""
        return list(self.positions.values())

    def get_total_exposure(self) -> dict[str, dict]:
        """Get exposure breakdown by symbol."""
        exposure = {}
        for symbol, pos in self.positions.items():
            exposure[symbol] = {
                "side": pos.side,
                "size_usd": pos.notional_value,
                "margin_usd": pos.margin_usd,
                "leverage": pos.leverage,
                "unrealized_pnl": pos.unrealized_pnl,
            }
        return exposure

    def check_liquidations(self) -> list[CryptoPosition]:
        """
        Check for positions near liquidation.

        Returns:
            List of positions at risk (within 10% of liquidation)
        """
        from tradingagents_crypto.agents.risk_mgmt.liquidation_scenator import calc_liquidation

        at_risk = []

        for pos in self.positions.values():
            result = calc_liquidation(
                direction=pos.side,
                entry_price=pos.entry_price,
                current_price=pos.mark_price,
                leverage=pos.leverage,
            )

            # Flag if within 10% of liquidation
            if result.distance_to_liq_pct < 0.10:
                at_risk.append(pos)

        return at_risk

    def _to_exposure_positions(self) -> list[Position]:
        """Convert CryptoPositions to ExposurePositions for check_exposure."""
        return [
            Position(
                symbol=pos.symbol,
                side=pos.side,
                size_usd=pos.notional_value,
                entry_price=pos.entry_price,
                current_price=pos.mark_price,
                leverage=pos.leverage,
            )
            for pos in self.positions.values()
        ]

    def get_summary(self) -> dict:
        """Get portfolio summary."""
        return {
            "total_equity": self.total_equity,
            "total_unrealized_pnl": self.total_unrealized_pnl,
            "total_realized_pnl": self.total_realized_pnl,
            "num_positions": len(self.positions),
            "positions": self.get_total_exposure(),
        }
