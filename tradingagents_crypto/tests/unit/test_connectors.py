"""
Unit tests for live trading connectors.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from tradingagents_crypto.trading.connectors.hyperliquid import (
    HyperliquidConnector,
    OrderRequest,
    OrderResponse,
)


class TestHyperliquidConnector:
    """Tests for HyperliquidConnector."""

    @pytest.fixture
    def connector(self):
        """Create a connector with mocked HTTP."""
        with patch("tradingagents_crypto.trading.connectors.hyperliquid.get_config") as mock_config:
            mock_cfg = MagicMock()
            mock_cfg.hyperliquid.testnet_url = "https://api.testnet"
            mock_cfg.hyperliquid.mainnet_url = "https://api.mainnet"
            mock_config.return_value = mock_cfg

            conn = HyperliquidConnector(testnet=True)
            conn._http = AsyncMock()
            yield conn

    @pytest.mark.asyncio
    async def test_init_uses_testnet_url(self, connector):
        """Test connector uses testnet URL by default."""
        assert "testnet" in connector.base_url

    @pytest.mark.asyncio
    async def test_place_order_success(self, connector):
        """Test successful order placement."""
        connector._http.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: {
                    "orderId": "ORDER_123",
                    "status": "filled",
                    "filledQty": 0.1,
                    "filledPrice": 50000.0,
                },
                raise_for_status=lambda: None,
            )
        )

        order = OrderRequest(
            symbol="BTC",
            side="long",
            size=0.1,
            price=50000.0,
        )
        result = await connector.place_order(order)

        assert result.order_id == "ORDER_123"
        assert result.status == "filled"
        assert result.filled_qty == 0.1

    @pytest.mark.asyncio
    async def test_place_order_http_error(self, connector):
        """Test order placement with HTTP error."""
        import httpx

        async def mock_post(*args, **kwargs):
            raise httpx.HTTPStatusError(
                "Server error",
                response=MagicMock(status_code=500),
                request=MagicMock(),
            )

        connector._http.post = mock_post

        order = OrderRequest(symbol="BTC", side="long", size=0.1)
        result = await connector.place_order(order)

        assert result.status == "pending"
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_cancel_order(self, connector):
        """Test cancelling an order."""
        connector._http.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: {"status": "cancelled"},
                raise_for_status=lambda: None,
            )
        )

        result = await connector.cancel_order("BTC", "ORDER_123")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_open_orders(self, connector):
        """Test getting open orders."""
        connector._http.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: {
                    "orders": [
                        {"orderId": "1", "symbol": "BTC", "side": "long"},
                        {"orderId": "2", "symbol": "ETH", "side": "short"},
                    ]
                },
                raise_for_status=lambda: None,
            )
        )

        orders = await connector.get_open_orders()
        assert len(orders) == 2

    @pytest.mark.asyncio
    async def test_get_open_orders_filtered(self, connector):
        """Test getting open orders filtered by symbol."""
        connector._http.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: {
                    "orders": [
                        {"orderId": "1", "symbol": "BTC", "side": "long"},
                        {"orderId": "2", "symbol": "ETH", "side": "short"},
                    ]
                },
                raise_for_status=lambda: None,
            )
        )

        btc_orders = await connector.get_open_orders(symbol="BTC")
        assert len(btc_orders) == 1
        assert btc_orders[0]["symbol"] == "BTC"

    @pytest.mark.asyncio
    async def test_get_positions(self, connector):
        """Test getting open positions."""
        connector._http.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: {
                    "positions": [
                        {"symbol": "BTC", "side": "long", "size": 0.1},
                    ]
                },
                raise_for_status=lambda: None,
            )
        )

        positions = await connector.get_positions()
        assert len(positions) == 1
        assert positions[0]["symbol"] == "BTC"

    @pytest.mark.asyncio
    async def test_close(self, connector):
        """Test closing the connector."""
        connector._http.aclose = AsyncMock()
        await connector.close()
        connector._http.aclose.assert_called_once()


class TestOrderRequest:
    """Tests for OrderRequest dataclass."""

    def test_creation_defaults(self):
        """Test OrderRequest with defaults."""
        order = OrderRequest(symbol="BTC", side="long")
        assert order.symbol == "BTC"
        assert order.side == "long"
        assert order.order_type == "market"
        assert order.reduce_only is False

    def test_creation_with_limit(self):
        """Test OrderRequest for limit order."""
        order = OrderRequest(
            symbol="ETH",
            side="short",
            order_type="limit",
            size=1.0,
            price=3000.0,
        )
        assert order.order_type == "limit"
        assert order.price == 3000.0


class TestOrderResponse:
    """Tests for OrderResponse dataclass."""

    def test_creation(self):
        """Test OrderResponse creation."""
        response = OrderResponse(
            order_id="ORDER_123",
            status="filled",
            filled_qty=0.1,
            filled_price=50000.0,
        )
        assert response.order_id == "ORDER_123"
        assert response.status == "filled"
        assert response.error is None

    def test_creation_with_error(self):
        """Test OrderResponse with error."""
        response = OrderResponse(
            order_id="ORDER_456",
            status="rejected",
            filled_qty=0.0,
            filled_price=0.0,
            error="Insufficient balance",
        )
        assert response.error == "Insufficient balance"
