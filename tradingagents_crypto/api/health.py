"""
FastAPI health check endpoints for Kubernetes probes.

Provides /health, /health/ready, and /health/live endpoints.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI

app = FastAPI()

# Simple TTL cache implementation (Python < 3.11 compatible)
_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL = 60.0


def _health_check_cache() -> dict:
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


def _do_health_check() -> dict:
    """Perform actual health checks on dependencies."""
    checks: dict = {}

    # Redis check
    try:
        import redis
        start = time.time()
        r = redis.Redis.from_url("redis://localhost:6379", socket_timeout=2)
        r.ping()
        checks["redis"] = {
            "status": "ok",
            "latency_ms": int((time.time() - start) * 1000),
        }
    except Exception as e:
        checks["redis"] = {"status": "error", "message": str(e)}

    # Hyperliquid API check
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


@app.get("/health")
def health():
    """Comprehensive health status."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "version": "1.0.0",
    }


@app.get("/health/ready")
def readiness():
    """Readiness check for dependency services."""
    checks = _health_check_cache()
    has_error = any(c.get("status") == "error" for c in checks.values())

    return {
        "status": "ready" if not has_error else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "checks": checks,
    }


@app.get("/health/live")
def liveness():
    """Liveness probe - process is alive."""
    return {
        "status": "live",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
    }
