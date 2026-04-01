"""
Paper trading mode for backtesting without real orders.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class PaperPosition:
    """Simulated position in paper trading."""
    symbol: str
    side: str  # long, short
    size: float
    entry_price: float
    current_price: float
    leverage: int
    opened_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PaperOrder:
    """Simulated order in paper trading."""
    order_id: str
    symbol: str
    side: str
    order_type: str  # market, limit
    size: float
    price: float | None = None
    filled_price: float | None = None
    status: str = "pending"  # pending, filled, cancelled
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    filled_at: datetime | None = None


class PaperTradingEngine:
    """Simulated trading engine for paper trading."""

    def __init__(self, initial_balance: float = 100_000.0):
        """Initialize paper trading engine.

        Args:
            initial_balance: Starting USD balance
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self._positions: dict[str, PaperPosition] = {}
        self._orders: dict[str, PaperOrder] = {}
        self._order_counter = 0
        self._lock = asyncio.Lock()

    async def get_balance(self) -> float:
        """Get current cash balance."""
        async with self._lock:
            return self.balance

    async def get_positions(self) -> list[PaperPosition]:
        """Get all open positions."""
        async with self._lock:
            return list(self._positions.values())

    async def get_position(self, symbol: str) -> PaperPosition | None:
        """Get position for a symbol."""
        async with self._lock:
            return self._positions.get(symbol)

    async def place_order(
        self,
        symbol: str,
        side: str,
        size: float,
        price: float | None = None,
        order_type: str = "market",
    ) -> PaperOrder:
        """Place a simulated order.

        Args:
            symbol: Trading symbol
            side: long or short
            size: Order size
            price: Limit price (for limit orders)
            order_type: market or limit

        Returns:
            PaperOrder instance
        """
        async with self._lock:
            self._order_counter += 1
            order_id = f"PAPER_{self._order_counter:06d}"
            order = PaperOrder(
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                size=size,
                price=price,
                filled_price=price if order_type == "market" else None,
            )
            self._orders[order_id] = order

            # Simulate market fill
            if order_type == "market":
                order.status = "filled"
                order.filled_at = datetime.now(timezone.utc)
                await self._fill_order(order)

            return order

    async def _fill_order(self, order: PaperOrder):
        """Internal: fill an order and update positions."""
        if order.status != "filled":
            return

        symbol = order.symbol
        current_price = order.filled_price or 0.0

        if symbol in self._positions:
            # Close existing position first
            old_pos = self._positions[symbol]
            pnl = self._calculate_pnl(old_pos, current_price)
            self.balance += pnl
            del self._positions[symbol]

        # Open new position if not close
        if order.side in ("long", "short"):
            position = PaperPosition(
                symbol=symbol,
                side=order.side,
                size=order.size,
                entry_price=current_price,
                current_price=current_price,
                leverage=1,
            )
            self._positions[symbol] = position

    async def close_position(self, symbol: str, current_price: float) -> dict:
        """Close a position at given price.

        Args:
            symbol: Symbol to close
            current_price: Current market price

        Returns:
            Result dict with PnL
        """
        async with self._lock:
            if symbol not in self._positions:
                return {"error": f"No position for {symbol}"}

            pos = self._positions[symbol]
            pnl = self._calculate_pnl(pos, current_price)
            self.balance += pnl

            del self._positions[symbol]

            return {
                "symbol": symbol,
                "pnl": pnl,
                "balance": self.balance,
            }

    async def update_prices(self, prices: dict[str, float]):
        """Update current prices for all positions.

        Args:
            prices: Dict mapping symbol to current price
        """
        async with self._lock:
            for symbol, price in prices.items():
                if symbol in self._positions:
                    self._positions[symbol].current_price = price

    def _calculate_pnl(self, position: PaperPosition, exit_price: float) -> float:
        """Calculate PnL for a position."""
        if position.side == "long":
            return (exit_price - position.entry_price) * position.size
        else:  # short
            return (position.entry_price - exit_price) * position.size

    async def get_orders(self, symbol: str | None = None) -> list[PaperOrder]:
        """Get order history."""
        async with self._lock:
            if symbol:
                return [o for o in self._orders.values() if o.symbol == symbol]
            return list(self._orders.values())

    async def get_unrealized_pnl(self) -> float:
        """Calculate total unrealized PnL across all positions."""
        async with self._lock:
            total = 0.0
            for pos in self._positions.values():
                total += self._calculate_pnl(pos, pos.current_price)
            return total

    async def reset(self):
        """Reset paper trading state to initial balance."""
        async with self._lock:
            self.balance = self.initial_balance
            self._positions.clear()
            self._orders.clear()
            self._order_counter = 0
