"""
Hyperliquid dataflows SQLite cache.

Provides TTL-based caching for HL API responses.
"""
import json
import logging
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class CacheManager:
    """
    SQLite-based cache with TTL support.

    Thread-safe for concurrent reads/writes.
    """

    def __init__(self, cache_dir: str | None = None):
        if cache_dir is None:
            cache_dir = os.path.join(
                os.path.dirname(__file__), "data_cache"
            )
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "hl_cache.db"
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(
                self.db_path, timeout=30
            )
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self):
        """Initialize database schema."""
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                expires_at REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_expires
            ON cache(expires_at)
        """)
        conn.commit()

    def get(self, key: str) -> Any | None:
        """
        Get cached value if exists and not expired.

        Returns None if not found or expired.
        """
        try:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT value, expires_at FROM cache WHERE key = ?",
                (key,),
            ).fetchone()

            if row is None:
                return None

            if time.time() > row["expires_at"]:
                # Expired, delete
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
                return None

            return json.loads(row["value"])
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl_seconds: int):
        """Set cache value with TTL in seconds."""
        if ttl_seconds <= 0:
            return  # Don't cache if TTL is 0

        try:
            conn = self._get_conn()
            expires_at = time.time() + ttl_seconds
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
                (key, json.dumps(value), expires_at),
            )
            conn.commit()
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")

    def delete(self, key: str):
        """Delete a specific cache entry."""
        try:
            conn = self._get_conn()
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")

    def clear_expired(self):
        """Remove all expired entries."""
        try:
            conn = self._get_conn()
            conn.execute(
                "DELETE FROM cache WHERE expires_at < ?",
                (time.time(),),
            )
            conn.commit()
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")

    def clear_all(self):
        """Remove all cache entries."""
        try:
            conn = self._get_conn()
            conn.execute("DELETE FROM cache")
            conn.commit()
        except Exception as e:
            logger.warning(f"Cache clear all error: {e}")

    @staticmethod
    def candle_key(
        symbol: str,
        interval: str,
        start_ms: int,
        end_ms: int,
    ) -> str:
        """Generate cache key for candle data."""
        return f"candle:{symbol}:{interval}:{start_ms}:{end_ms}"

    @staticmethod
    def funding_key(symbol: str) -> str:
        """Generate cache key for funding data."""
        return f"funding:{symbol}"

    @staticmethod
    def oi_key(symbol: str) -> str:
        """Generate cache key for OI data."""
        return f"oi:{symbol}"
