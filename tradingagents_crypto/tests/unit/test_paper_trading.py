"""
Unit tests for paper trading engine.
"""
import pytest
import asyncio
from tradingagents_crypto.trading.modes.paper import (
    PaperTradingEngine,
    PaperPosition,
    PaperOrder,
)


class TestPaperTradingEngine:
    """Tests for PaperTradingEngine."""

    @pytest.fixture
    def engine(self):
        """Create a paper trading engine."""
        return PaperTradingEngine(initial_balance=100_000.0)

    @pytest.mark.asyncio
    async def test_initial_balance(self, engine):
        """Test initial balance is set correctly."""
        balance = await engine.get_balance()
        assert balance == 100_000.0

    @pytest.mark.asyncio
    async def test_place_market_order(self, engine):
        """Test placing a market order."""
        order = await engine.place_order(
            symbol="BTC",
            side="long",
            size=0.1,
            price=50_000.0,
            order_type="market",
        )
        assert order.status == "filled"
        assert order.filled_price == 50_000.0

    @pytest.mark.asyncio
    async def test_place_limit_order(self, engine):
        """Test placing a limit order (not filled until price met)."""
        order = await engine.place_order(
            symbol="ETH",
            side="long",
            size=1.0,
            price=3000.0,
            order_type="limit",
        )
        assert order.status == "pending"
        assert order.filled_price is None

    @pytest.mark.asyncio
    async def test_position_opened_after_market_order(self, engine):
        """Test that a position is opened after market order."""
        await engine.place_order(
            symbol="BTC",
            side="long",
            size=0.1,
            price=50_000.0,
            order_type="market",
        )

        position = await engine.get_position("BTC")
        assert position is not None
        assert position.side == "long"
        assert position.size == 0.1
        assert position.entry_price == 50_000.0

    @pytest.mark.asyncio
    async def test_close_position(self, engine):
        """Test closing a position."""
        await engine.place_order(
            symbol="BTC",
            side="long",
            size=0.1,
            price=50_000.0,
            order_type="market",
        )

        result = await engine.close_position("BTC", 55_000.0)
        assert "pnl" in result
        assert result["pnl"] == 500.0  # (55k - 50k) * 0.1 = 500

    @pytest.mark.asyncio
    async def test_short_position_pnl(self, engine):
        """Test PnL calculation for short position."""
        await engine.place_order(
            symbol="BTC",
            side="short",
            size=0.1,
            price=50_000.0,
            order_type="market",
        )

        result = await engine.close_position("BTC", 45_000.0)
        assert result["pnl"] == 500.0  # (50k - 45k) * 0.1 = 500

    @pytest.mark.asyncio
    async def test_balance_updated_after_close(self, engine):
        """Test that balance is updated after closing position."""
        await engine.place_order(
            symbol="BTC",
            side="long",
            size=0.1,
            price=50_000.0,
            order_type="market",
        )

        initial_balance = await engine.get_balance()
        await engine.close_position("BTC", 55_000.0)
        new_balance = await engine.get_balance()

        assert new_balance == initial_balance + 500.0

    @pytest.mark.asyncio
    async def test_get_positions(self, engine):
        """Test getting all positions."""
        await engine.place_order("BTC", "long", 0.1, 50_000.0, "market")
        await engine.place_order("ETH", "long", 1.0, 3000.0, "market")

        positions = await engine.get_positions()
        assert len(positions) == 2

    @pytest.mark.asyncio
    async def test_update_prices(self, engine):
        """Test updating position prices."""
        await engine.place_order("BTC", "long", 0.1, 50_000.0, "market")
        await engine.update_prices({"BTC": 60_000.0})

        position = await engine.get_position("BTC")
        assert position.current_price == 60_000.0

    @pytest.mark.asyncio
    async def test_get_unrealized_pnl(self, engine):
        """Test calculating unrealized PnL."""
        await engine.place_order("BTC", "long", 0.1, 50_000.0, "market")
        await engine.update_prices({"BTC": 55_000.0})

        pnl = await engine.get_unrealized_pnl()
        assert pnl == 500.0

    @pytest.mark.asyncio
    async def test_reset(self, engine):
        """Test resetting the engine."""
        await engine.place_order("BTC", "long", 0.1, 50_000.0, "market")
        await engine.reset()

        assert await engine.get_balance() == 100_000.0
        assert len(await engine.get_positions()) == 0

    @pytest.mark.asyncio
    async def test_get_orders(self, engine):
        """Test getting order history."""
        await engine.place_order("BTC", "long", 0.1, 50_000.0, "market")
        await engine.place_order("ETH", "long", 1.0, 3000.0, "market")

        orders = await engine.get_orders()
        assert len(orders) == 2

    @pytest.mark.asyncio
    async def test_get_orders_by_symbol(self, engine):
        """Test filtering orders by symbol."""
        await engine.place_order("BTC", "long", 0.1, 50_000.0, "market")
        await engine.place_order("ETH", "long", 1.0, 3000.0, "market")

        btc_orders = await engine.get_orders(symbol="BTC")
        assert len(btc_orders) == 1
        assert btc_orders[0].symbol == "BTC"


class TestPaperPosition:
    """Tests for PaperPosition dataclass."""

    def test_creation(self):
        """Test creating a PaperPosition."""
        pos = PaperPosition(
            symbol="BTC",
            side="long",
            size=0.1,
            entry_price=50_000.0,
            current_price=50_000.0,
            leverage=5,
        )
        assert pos.symbol == "BTC"
        assert pos.side == "long"
        assert pos.leverage == 5


class TestPaperOrder:
    """Tests for PaperOrder dataclass."""

    def test_creation(self):
        """Test creating a PaperOrder."""
        order = PaperOrder(
            order_id="PAPER_001",
            symbol="BTC",
            side="long",
            order_type="market",
            size=0.1,
            price=50_000.0,
        )
        assert order.order_id == "PAPER_001"
        assert order.status == "pending"

    def test_default_status(self):
        """Test default status is pending."""
        order = PaperOrder(
            order_id="TEST",
            symbol="BTC",
            side="long",
            order_type="market",
            size=0.1,
            price=50_000.0,
        )
        assert order.status == "pending"
