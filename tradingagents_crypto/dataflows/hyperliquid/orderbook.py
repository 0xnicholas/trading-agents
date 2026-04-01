"""
Hyperliquid orderbook data.

High-level functions for L2 orderbook data.
"""
import logging
from .api import HLClient

logger = logging.getLogger(__name__)

# Note: Orderbook is real-time, no caching (TTL = 0)


def get_orderbook(
    symbol: str,
    depth: int = 20,
    client: HLClient | None = None,
) -> dict:
    """
    Get L2 orderbook snapshot for a symbol.

    Args:
        symbol: Coin name (e.g., "BTC")
        depth: Number of levels per side (default: 20)
        client: Optional HLClient instance

    Returns:
        Dict with keys:
        - coin: Symbol name
        - time: Unix milliseconds
        - bids: [[price, size], ...] sorted by price descending
        - asks: [[price, size], ...] sorted by price ascending
    """
    if client is None:
        client = HLClient()

    snapshot = client.get_l2_snapshot(symbol)

    coin = snapshot.get("coin", symbol)
    time_ms = int(snapshot.get("time", 0))
    levels = snapshot.get("levels", [[], []])

    # bids = levels[0], asks = levels[1]
    raw_bids = levels[0] if len(levels) > 0 else []
    raw_asks = levels[1] if len(levels) > 1 else []

    # Parse into [[price, size], ...] format
    bids = [
        [float(b.get("px", 0)), float(b.get("sz", 0))]
        for b in raw_bids[:depth]
    ]
    asks = [
        [float(a.get("px", 0)), float(a.get("sz", 0))]
        for a in raw_asks[:depth]
    ]

    # Sort: bids descending (best bid first), asks ascending (best ask first)
    bids = sorted(bids, key=lambda x: -x[0]) if bids else []
    asks = sorted(asks, key=lambda x: x[0]) if asks else []

    return {
        "coin": coin,
        "time": time_ms,
        "bids": bids,
        "asks": asks,
    }


def calc_orderbook_imbalance(
    orderbook: dict,
) -> float:
    """
    Calculate orderbook imbalance ratio.

    Args:
        orderbook: Dict from get_orderbook()

    Returns:
        Ratio of bid_depth / ask_depth.
        > 1.0 = more bids (bullish)
        < 1.0 = more asks (bearish)
        = 1.0 = balanced
    """
    bids = orderbook.get("bids", [])
    asks = orderbook.get("asks", [])

    bid_depth = sum(size for _, size in bids)
    ask_depth = sum(size for _, size in asks)

    if ask_depth == 0:
        return 1.0  # Avoid division by zero

    return bid_depth / ask_depth


def calc_spread_bps(
    orderbook: dict,
) -> float:
    """
    Calculate bid-ask spread in basis points.

    Args:
        orderbook: Dict from get_orderbook()

    Returns:
        Spread in bps: (ask - bid) / mid * 10000
    """
    bids = orderbook.get("bids", [])
    asks = orderbook.get("asks", [])

    if not bids or not asks:
        return 0.0

    best_bid = bids[0][0] if bids else 0.0
    best_ask = asks[0][0] if asks else 0.0

    if best_bid == 0 or best_ask == 0:
        return 0.0

    mid = (best_bid + best_ask) / 2
    spread = best_ask - best_bid
    bps = (spread / mid) * 10000

    return bps
