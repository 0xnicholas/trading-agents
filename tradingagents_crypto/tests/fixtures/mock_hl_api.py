"""
Mock fixtures for Hyperliquid API responses.

These fixtures are used in unit and integration tests.
"""
import time
from datetime import datetime, timezone


def mock_all_mids():
    """Mock all mids response."""
    return {
        "BTC": "67000.0",
        "ETH": "3500.0",
        "SOL": "150.0",
        "DOGE": "0.15",
        "kPEPE": "0.00012",
    }


def mock_meta_and_asset_ctxs():
    """Mock meta_and_asset_ctxs response.

    Returns (meta, asset_ctxs) tuple as SDK does.
    """
    meta = {
        "universe": [
            {"name": "BTC", "szDecimals": 5},
            {"name": "ETH", "szDecimals": 4},
            {"name": "SOL", "szDecimals": 3},
        ]
    }
    asset_ctxs = [
        {
            "dayNtlVlm": "1234567890.0",
            "funding": "0.0001",
            "openInterest": "500000000.0",
            "prevDayPx": "66000.0",
            "markPx": "67200.0",
            "midPx": "67180.0",
            "oraclePx": "67100.0",
            "premium": "0.00005",
            "impactPxs": ["66900.0", "67500.0"],
            "dayBaseVlm": "12345.6",
        },
        {
            "dayNtlVlm": "987654321.0",
            "funding": "0.00008",
            "openInterest": "200000000.0",
            "prevDayPx": "3450.0",
            "markPx": "3550.0",
            "midPx": "3545.0",
            "oraclePx": "3540.0",
            "premium": "0.00003",
            "impactPxs": ["3520.0", "3580.0"],
            "dayBaseVlm": "9876.5",
        },
        {
            "dayNtlVlm": "456789012.0",
            "funding": "0.00015",
            "openInterest": "80000000.0",
            "prevDayPx": "145.0",
            "markPx": "152.0",
            "midPx": "151.5",
            "oraclePx": "151.0",
            "premium": "0.0001",
            "impactPxs": ["149.0", "155.0"],
            "dayBaseVlm": "4567.8",
        },
    ]
    return meta, asset_ctxs


def mock_candles_btc_1h():
    """Mock 1h candles for BTC (7 days = 168 candles)."""
    now = int(time.time())
    hour = 3600
    candles = []
    base_price = 67000.0

    for i in range(168):
        ts = now - (168 - i) * hour
        # Generate realistic-ish price movement
        noise = (i % 24) * 10 - 120  # Daily pattern
        close = base_price + noise + (i * 2)
        candles.append({
            "T": ts * 1000,  # milliseconds
            "t": ts,  # seconds
            "o": str(close - 50),
            "h": str(close + 100),
            "l": str(close - 100),
            "c": str(close),
            "v": str(1000 + i * 10),
            "n": 150 + i,
            "s": "ok",
        })

    return candles


def mock_l2_snapshot_btc():
    """Mock L2 orderbook snapshot for BTC."""
    return {
        "coin": "BTC",
        "time": int(time.time() * 1000),
        "levels": [
            [  # bids
                {"n": 1, "px": "67100.0", "sz": "1.5"},
                {"n": 2, "px": "67000.0", "sz": "2.3"},
                {"n": 3, "px": "66900.0", "sz": "3.1"},
                {"n": 4, "px": "66800.0", "sz": "1.8"},
                {"n": 5, "px": "66700.0", "sz": "2.0"},
            ],
            [  # asks
                {"n": 1, "px": "67200.0", "sz": "1.2"},
                {"n": 2, "px": "67300.0", "sz": "2.0"},
                {"n": 3, "px": "67400.0", "sz": "1.5"},
                {"n": 4, "px": "67500.0", "sz": "2.2"},
                {"n": 5, "px": "67600.0", "sz": "1.0"},
            ],
        ],
    }


def mock_funding_history_btc():
    """Mock funding history for BTC (24 hours, 3 records at 8h intervals)."""
    now = int(time.time())
    hour = 3600
    records = []

    rates = [0.0001, 0.00012, 0.00008]
    premiums = [0.00005, 0.00006, 0.00004]

    for i, (rate, premium) in enumerate(zip(rates, premiums)):
        ts = now - (3 - i) * 8 * hour
        records.append({
            "coin": "BTC",
            "fundingRate": str(rate),
            "premium": str(premium),
            "time": ts * 1000,  # milliseconds
        })

    return records
