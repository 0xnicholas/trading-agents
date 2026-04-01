"""
Unit tests for cache.py
"""
import pytest
import time
import tempfile
import shutil
from pathlib import Path

from tradingagents_crypto.dataflows.hyperliquid.cache import CacheManager


@pytest.fixture
def cache_dir(tmp_path):
    """Create a temporary cache directory."""
    cache_path = tmp_path / "test_cache"
    yield str(cache_path)
    # Cleanup
    if Path(cache_path).exists():
        shutil.rmtree(cache_path)


@pytest.fixture
def cache(cache_dir):
    """Create CacheManager with temp directory."""
    return CacheManager(cache_dir=cache_dir)


class TestCacheManager:
    """Tests for CacheManager."""

    def test_set_and_get(self, cache):
        """Test basic set and get."""
        cache.set("test_key", {"data": 123}, ttl_seconds=3600)
        result = cache.get("test_key")
        assert result == {"data": 123}

    def test_get_nonexistent(self, cache):
        """Test getting non-existent key returns None."""
        assert cache.get("nonexistent") is None

    def test_expired_key_returns_none(self, cache):
        """Test expired key returns None."""
        cache.set("expired_key", {"data": "expired"}, ttl_seconds=1)
        time.sleep(1.1)  # Wait for expiration
        assert cache.get("expired_key") is None

    def test_ttl_zero_not_cached(self, cache):
        """Test TTL of 0 does not cache."""
        cache.set("zero_ttl", {"data": "should not cache"}, ttl_seconds=0)
        assert cache.get("zero_ttl") is None

    def test_delete(self, cache):
        """Test deleting a key."""
        cache.set("to_delete", {"data": "delete me"}, ttl_seconds=3600)
        cache.delete("to_delete")
        assert cache.get("to_delete") is None

    def test_clear_expired(self, cache):
        """Test clearing expired entries."""
        # Set one with short TTL
        cache.set("short_lived", {"data": "expire"}, ttl_seconds=1)
        # Set one with long TTL
        cache.set("long_lived", {"data": "keep"}, ttl_seconds=3600)

        time.sleep(1.1)
        cache.clear_expired()

        assert cache.get("short_lived") is None
        assert cache.get("long_lived") == {"data": "keep"}

    def test_clear_all(self, cache):
        """Test clearing all cache."""
        cache.set("key1", {"data": 1}, ttl_seconds=3600)
        cache.set("key2", {"data": 2}, ttl_seconds=3600)
        cache.clear_all()
        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestCacheKeys:
    """Tests for cache key generation methods."""

    def test_candle_key(self):
        """Test candle cache key format."""
        key = CacheManager.candle_key("BTC", "1h", 1710000000000, 1710003600000)
        assert key == "candle:BTC:1h:1710000000000:1710003600000"

    def test_funding_key(self):
        """Test funding cache key format."""
        key = CacheManager.funding_key("BTC")
        assert key == "funding:BTC"

    def test_oi_key(self):
        """Test OI cache key format."""
        key = CacheManager.oi_key("ETH")
        assert key == "oi:ETH"

    def test_keys_unique(self):
        """Test different keys generate unique keys."""
        key1 = CacheManager.candle_key("BTC", "1h", 1000, 2000)
        key2 = CacheManager.candle_key("ETH", "1h", 1000, 2000)
        assert key1 != key2

        key3 = CacheManager.candle_key("BTC", "4h", 1000, 2000)
        key4 = CacheManager.candle_key("BTC", "1h", 1000, 2000)
        assert key3 != key4
