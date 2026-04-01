#!/usr/bin/env python3
"""
Hyperliquid SDK Connection Test
验证 SDK 是否能正常连接并获取数据
"""
from hyperliquid.info import Info
from hyperliquid.utils import constants


def test_connection():
    print("Testing Hyperliquid SDK connection...")
    
    # Test 1: Connect to mainnet
    print("\n[1] Connecting to MAINNET_API_URL...")
    info = Info(constants.MAINNET_API_URL, skip_ws=True)
    print("    ✅ Connected")
    
    # Test 2: Get all mids (all coin prices)
    print("\n[2] Fetching all mids (coin prices)...")
    mids = info.all_mids()
    print(f"    ✅ Retrieved {len(mids)} coins")
    for coin in ["BTC", "ETH", "SOL"]:
        if coin in mids:
            print(f"    {coin}: ${mids[coin]}")
    
    # Test 3: Get meta and asset contexts
    print("\n[3] Fetching meta and asset contexts...")
    meta, asset_ctxs = info.meta_and_asset_ctxs()
    print(f"    ✅ Retrieved {len(meta['universe'])} coins")
    print(f"    Sample: {meta['universe'][0]}")
    
    # Test 4: Get funding history for BTC
    print("\n[4] Fetching BTC funding history...")
    import time
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - 86400000  # 24 hours ago
    funding = info.funding_history("BTC", start_ms, end_ms)
    print(f"    ✅ Retrieved {len(funding)} funding records")
    if funding:
        latest = funding[-1]
        print(f"    Latest: rate={latest.get('fundingRate')}, premium={latest.get('premium')}")
    
    # Test 5: Get L2 snapshot for BTC
    print("\n[5] Fetching BTC orderbook (L2 snapshot)...")
    l2 = info.l2_snapshot("BTC")
    print(f"    ✅ Retrieved orderbook for {l2.get('coin')}")
    bids = l2.get("levels", [[], []])[0]
    asks = l2.get("levels", [[], []])[1]
    print(f"    Top bid: {bids[0] if bids else 'N/A'}")
    print(f"    Top ask: {asks[0] if asks else 'N/A'}")
    
    print("\n" + "=" * 50)
    print("All tests passed! SDK is ready.")
    print("=" * 50)


if __name__ == "__main__":
    test_connection()
