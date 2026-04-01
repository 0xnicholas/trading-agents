"""
Hyperliquid live trading connector.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx

from tradingagents_crypto.config import get_config


@dataclass
class OrderRequest:
    """Order request for live trading."""
    symbol: str
    side: str  # long, short, close
    order_type: str = "market"  # market, limit
    size: float | None = None
    price: float | None = None
    reduce_only: bool = False


@dataclass
class OrderResponse:
    """Order response from exchange."""
    order_id: str
    status: str  # filled, pending, cancelled, rejected
    filled_qty: float
    filled_price: float
    error: str | None = None


class HyperliquidConnector:
    """Connector for Hyperliquid live trading API."""

    def __init__(self, testnet: bool = True):
        """Initialize Hyperliquid connector.

        Args:
            testnet: Use testnet (default True for safety)
        """
        self.config = get_config()
        hl_config = self.config.hyperliquid
        self.base_url = hl_config.testnet_url if testnet else hl_config.mainnet_url
        self._http = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client."""
        await self._http.aclose()

    async def get_account_summary(self) -> dict:
        """Get account summary (balance, positions, etc.)."""
        payload = {
            "type": "accountSummary",
            "user": self._get_wallet_address(),
        }
        response = await self._post(payload)
        return response

    async def place_order(self, order: OrderRequest) -> OrderResponse:
        """Place a live order.

        Args:
            order: OrderRequest with order details

        Returns:
            OrderResponse with execution details
        """
        payload = {
            "type": "order",
            "user": self._get_wallet_address(),
            "order": {
                "symbol": order.symbol,
                "side": order.side,
                "orderType": order.order_type,
                "size": order.size,
                "price": order.price,
                "reduceOnly": order.reduce_only,
            },
        }
        response = await self._post(payload)

        return OrderResponse(
            order_id=response.get("orderId", ""),
            status=response.get("status", "pending"),
            filled_qty=response.get("filledQty", 0.0),
            filled_price=response.get("filledPrice", 0.0),
            error=response.get("error"),
        )

    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel a pending order.

        Args:
            symbol: Trading symbol
            order_id: Order ID to cancel

        Returns:
            True if cancelled, False otherwise
        """
        payload = {
            "type": "cancel",
            "user": self._get_wallet_address(),
            "symbol": symbol,
            "orderId": order_id,
        }
        response = await self._post(payload)
        return response.get("status") == "cancelled"

    async def get_open_orders(self, symbol: str | None = None) -> list[dict]:
        """Get open orders.

        Args:
            symbol: Optional symbol filter

        Returns:
            List of open orders
        """
        payload = {
            "type": "openOrders",
            "user": self._get_wallet_address(),
        }
        response = await self._post(payload)
        orders = response.get("orders", [])

        if symbol:
            orders = [o for o in orders if o.get("symbol") == symbol]
        return orders

    async def get_positions(self) -> list[dict]:
        """Get all open positions."""
        payload = {
            "type": "positions",
            "user": self._get_wallet_address(),
        }
        response = await self._post(payload)
        return response.get("positions", [])

    async def _post(self, payload: dict) -> dict:
        """Send POST request to Hyperliquid API."""
        try:
            response = await self._http.post(
                f"{self.base_url}/api/v1/execute",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except httpx.RequestError as e:
            return {"error": f"Request error: {str(e)}"}

    def _get_wallet_address(self) -> str:
        """Get wallet address from config (placeholder)."""
        # In production, this would read from wallet/secret manager
        return "0x0000000000000000000000000000000000000000"
