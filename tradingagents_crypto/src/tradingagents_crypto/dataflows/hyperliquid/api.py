"""
Hyperliquid API client.

Wraps hyperliquid-python-sdk Info API.
"""
__all__ = ['HLClient', 'get_all_mids', 'get_meta_and_asset_ctxs', 'get_candles', 'get_funding_history', 'get_l2_snapshot', 'get_recent_trades']
import logging
from typing import Any

from hyperliquid.info import Info
from hyperliquid.utils import constants

from .utils import now_ms, calc_time_range, is_valid_interval

logger = logging.getLogger(__name__)


class HLClient:
    """
    Hyperliquid Info API client.

    Wraps SDK Info class with convenience methods.
    """

    def __init__(
        self,
        base_url: str = constants.MAINNET_API_URL,
        skip_ws: bool = True,
    ):
        """
        Initialize HL client.

        Args:
            base_url: API URL (MAINNET_API_URL or TESTNET_API_URL)
            skip_ws: Skip WebSocket (we only use REST)
        """
        self.info = Info(base_url, skip_ws=skip_ws)
        self.base_url = base_url

    def get_all_mids(self) -> dict[str, str]:
        """Get all coin mid prices."""
        return self.info.all_mids()

    def get_meta_and_asset_ctxs(self) -> tuple[dict, list[dict]]:
        """
        Get meta and asset contexts.

        Returns:
            Tuple of (meta, asset_ctxs):
            - meta: {"universe": [{"name": str, "szDecimals": int}, ...]}
            - asset_ctxs: List[PerpAssetCtx]
        """
        return self.info.meta_and_asset_ctxs()

    def get_candles(
        self,
        symbol: str,
        interval: str,
        start_time_ms: int,
        end_time_ms: int,
    ) -> list[dict]:
        """
        Get candlestick data.

        Args:
            symbol: Coin name (e.g., "BTC")
            interval: "1h", "4h", or "1d"
            start_time_ms: Start time in Unix milliseconds
            end_time_ms: End time in Unix milliseconds

        Returns:
            List of candle dicts with keys: T, o, h, l, c, v, n
        """
        if not is_valid_interval(interval):
            raise ValueError(f"Invalid interval: {interval}")

        return self.info.candles_snapshot(
            symbol, interval, start_time_ms, end_time_ms
        )

    def get_funding_history(
        self,
        symbol: str,
        start_time_ms: int,
        end_time_ms: int | None = None,
    ) -> list[dict]:
        """
        Get funding rate history.

        Args:
            symbol: Coin name (e.g., "BTC")
            start_time_ms: Start time in Unix milliseconds
            end_time_ms: End time in Unix milliseconds

        Returns:
            List of funding records with keys: coin, fundingRate, premium, time
        """
        if end_time_ms is None:
            end_time_ms = now_ms()

        return self.info.funding_history(symbol, start_time_ms, end_time_ms)

    def get_l2_snapshot(self, symbol: str) -> dict:
        """
        Get L2 orderbook snapshot.

        Args:
            symbol: Coin name (e.g., "BTC")

        Returns:
            Dict with keys: coin, levels (bids, asks), time
        """
        return self.info.l2_snapshot(symbol)

    def get_recent_trades(self, symbol: str, limit: int = 100, lookback_ms: int = 3600_000) -> list[dict]:
        """
        Get recent trades.

        Args:
            symbol: Coin name
            limit: Max number of trades
            lookback_ms: Lookback window in milliseconds (default: 1 hour)

        Returns:
            List of trade dicts
        """
        # Note: SDK may not have this method directly
        # Falls back to candles with n (num trades) field
        end_ms = now_ms()
        start_ms = end_ms - lookback_ms  # Configurable lookback
        candles = self.get_candles(symbol, "1h", start_ms, end_ms)
        return [{"n": c.get("n", 0), "px": c.get("c"), "sz": c.get("v")}
                for c in candles if c.get("n", 0) > 0]
