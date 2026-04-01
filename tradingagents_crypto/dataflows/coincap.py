"""
CoinCap API client.

Used as primary data source for:
- ETH/SOL prices
- BTC dominance
- Stablecoin supplies
- On-chain metrics

API Docs: https://docs.coincap.io/
Base URL: https://api.coincap.io/v2
Rate Limit: 300 requests/minute
"""
import logging
from typing import Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from tradingagents_crypto.dataflows.hyperliquid.cache import CacheManager

logger = logging.getLogger(__name__)

DEFAULT_TTL = 300  # 5 minutes


class CoinCapClient:
    """CoinCap API client with caching."""

    BASE_URL = "https://api.coincap.io/v2"

    def __init__(self, cache: CacheManager | None = None):
        self.cache = cache or CacheManager()
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        """Make a GET request with retry."""
        url = f"{self.BASE_URL}{endpoint}"
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_asset(self, asset_id: str) -> dict | None:
        """
        Get asset data by ID.

        Args:
            asset_id: e.g., "bitcoin", "ethereum", "solana", "tether", "usd-coin"

        Returns:
            Asset data dict or None if not found
        """
        cache_key = f"coincap:asset:{asset_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            data = self._get(f"/assets/{asset_id}")
            result = data.get("data")
            if result:
                self.cache.set(cache_key, result, DEFAULT_TTL)
            return result
        except Exception as e:
            logger.warning(f"CoinCap get_asset({asset_id}) failed: {e}")
            return None

    def get_eth_price(self) -> dict:
        """
        Get ETH price and related data.

        Returns:
            Dict with priceUsd, changePercent24hr, etc.
        """
        cache_key = "coincap:eth_price"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        asset = self.get_asset("ethereum")
        result = {
            "price_usd": float(asset.get("priceUsd", 0)) if asset else 0.0,
            "change_24h_pct": float(asset.get("changePercent24Hr", 0)) if asset else 0.0,
            "market_cap": float(asset.get("marketCapUsd", 0)) if asset else 0.0,
            "volume_24h": float(asset.get("volumeUsd24Hr", 0)) if asset else 0.0,
            "rank": int(asset.get("rank", 0)) if asset else 0,
            "confidence": 0.75,  # CoinCap free API
        }
        self.cache.set(cache_key, result, DEFAULT_TTL)
        return result

    def get_sol_price(self) -> dict:
        """Get SOL price and related data."""
        cache_key = "coincap:sol_price"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        asset = self.get_asset("solana")
        result = {
            "price_usd": float(asset.get("priceUsd", 0)) if asset else 0.0,
            "change_24h_pct": float(asset.get("changePercent24Hr", 0)) if asset else 0.0,
            "market_cap": float(asset.get("marketCapUsd", 0)) if asset else 0.0,
            "volume_24h": float(asset.get("volumeUsd24Hr", 0)) if asset else 0.0,
            "rank": int(asset.get("rank", 0)) if asset else 0,
            "confidence": 0.8,  # CoinCap, slightly higher than ETH
        }
        self.cache.set(cache_key, result, DEFAULT_TTL)
        return result

    def get_btc_dominance(self) -> float:
        """
        Calculate BTC dominance from market caps.

        Returns:
            BTC dominance as percentage (e.g., 52.3)
        """
        cache_key = "coincap:btc_dominance"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            # Get top assets to calculate total market cap
            data = self._get("/assets?limit=100")
            assets = data.get("data", [])

            btc_cap = 0.0
            total_cap = 0.0

            for asset in assets:
                cap = float(asset.get("marketCapUsd", 0))
                total_cap += cap
                if asset.get("id") == "bitcoin":
                    btc_cap = cap

            dominance = (btc_cap / total_cap * 100) if total_cap > 0 else 0.0
            dominance = round(dominance, 2)

            # Cache longer - BTC dominance doesn't change frequently
            self.cache.set(cache_key, dominance, 600)  # 10 min
            return dominance

        except Exception as e:
            logger.warning(f"CoinCap get_btc_dominance failed: {e}")
            return 0.0

    def get_stablecoin_supplies(self) -> dict:
        """
        Get USDT and USDC supply data.

        Returns:
            Dict with tether_supply, usd_coin_supply, change_24h
        """
        cache_key = "coincap:stablecoins"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            tether = self.get_asset("tether")  # USDT
            usdc = self.get_asset("usd-coin")  # USDC

            tether_supply = float(tether.get("supply", 0)) if tether else 0.0
            usdc_supply = float(usdc.get("supply", 0)) if usdc else 0.0

            # 24h change
            tether_change = float(tether.get("changePercent24Hr", 0)) if tether else 0.0
            usdc_change = float(usdc.get("changePercent24Hr", 0)) if usdc else 0.0

            result = {
                "tether_supply": tether_supply,
                "usd_coin_supply": usdc_supply,
                "total_supply": tether_supply + usdc_supply,
                "tether_change_24h": tether_change,
                "usdc_change_24h": usdc_change,
                "confidence": 0.5,  # Approximation only
            }

            self.cache.set(cache_key, result, DEFAULT_TTL)
            return result

        except Exception as e:
            logger.warning(f"CoinCap get_stablecoin_supplies failed: {e}")
            return {
                "tether_supply": 0.0,
                "usd_coin_supply": 0.0,
                "total_supply": 0.0,
                "confidence": 0.3,
            }

    def get_eth_staking_ratio(self) -> float:
        """
        Get ETH staking ratio (approximation).

        Note: CoinCap doesn't have direct staking data,
        this is an approximation based on supplied vs market cap.
        """
        cache_key = "coincap:eth_staking_ratio"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            eth = self.get_asset("ethereum")
            if not eth:
                return 0.0

            # Approximation: CoinCap doesn't expose staking directly
            # Use circulating supply vs max supply as proxy
            supply = float(eth.get("supply", 0))
            max_supply = float(eth.get("maxSupply", 0)) or 120_000_000  # ETH max ~120M

            # If circulating is close to max, less staked
            # This is very rough - should use a dedicated staking API
            ratio = min(supply / max_supply, 1.0) if max_supply > 0 else 0.0

            self.cache.set(cache_key, ratio, DEFAULT_TTL)
            return ratio

        except Exception as e:
            logger.warning(f"CoinCap get_eth_staking_ratio failed: {e}")
            return 0.0
