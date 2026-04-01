"""
FastAPI health check endpoints for Kubernetes probes.

Provides /health, /health/ready, and /health/live endpoints.
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

# Dynamic version from environment variable (falls back to "1.0.0" for backward compat)
APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")
_CACHE_TTL = 60.0

# Module-level cache (used by tests for cache invalidation)
_cache: dict = {}

# Connection pool for health checks
_redis_pool: Any = None


def _get_redis_pool():
    """Get or create a shared Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        import redis
        _redis_pool = redis.Redis.from_url(
            "redis://localhost:6379",
            socket_timeout=2,
            socket_connect_timeout=2,
            max_connections=5,
        )
    return _redis_pool


def _do_health_check() -> dict:
    """Perform actual health checks on dependencies."""
    checks: dict = {}

    # Redis check (reuses connection pool)
    try:
        import redis
        start = time.time()
        r = _get_redis_pool()
        r.ping()
        checks["redis"] = {
            "status": "ok",
            "latency_ms": int((time.time() - start) * 1000),
        }
    except Exception as e:
        checks["redis"] = {"status": "error", "message": str(e)}

    # Hyperliquid API check (no persistent connection needed)
    try:
        from tradingagents_crypto.dataflows.hyperliquid import Hyperliquid
        start = time.time()
        hl = Hyperliquid()
        hl.get_wallet_balance()
        checks["hyperliquid"] = {
            "status": "ok",
            "latency_ms": int((time.time() - start) * 1000),
        }
    except Exception as e:
        checks["hyperliquid"] = {"status": "error", "message": str(e)}

    # LLM (connection only, no actual call)
    try:
        from tradingagents_crypto.config import get_config
        get_config()
        checks["llm"] = {"status": "ok", "latency_ms": 0}
    except Exception as e:
        checks["llm"] = {"status": "error", "message": str(e)}

    return checks


def _health_check_cached() -> dict:
    """60-second cached health check results."""
    global _cache
    now = time.time()
    if "checks" in _cache:
        cached_time, cached_result = _cache["checks"]
        if now - cached_time < _CACHE_TTL:
            return cached_result
    result = _do_health_check()
    _cache["checks"] = (now, result)
    return result


@app.get("/health")
def health():
    """Comprehensive health status."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "version": APP_VERSION,
    }


@app.get("/health/ready")
def readiness():
    """Readiness check for dependency services."""
    checks = _health_check_cached()
    has_error = any(c.get("status") == "error" for c in checks.values())

    status = "ready" if not has_error else "degraded"
    return JSONResponse(
        status_code=503 if has_error else 200,
        content={
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "checks": checks,
        },
    )


@app.get("/health/live")
def liveness():
    """Liveness probe - process is alive."""
    return {
        "status": "live",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
    }
