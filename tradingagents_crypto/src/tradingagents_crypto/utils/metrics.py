"""
Prometheus metrics definitions for trading system.

Provides counters, gauges, and histograms for trading, performance, and system metrics.
"""
from __future__ import annotations

import time
from typing import Callable

import psutil
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


# === Trading Metrics ===
orders_total = Counter(
    "trading_orders_total",
    "Total number of orders",
    ["symbol", "side", "result"],  # result: filled/rejected/cancelled
)

pnl_gauge = Gauge(
    "trading_pnl_total",
    "Total PnL in USD",
    ["symbol"],
)

position_size = Gauge(
    "trading_position_size",
    "Current position size in USD",
    ["symbol"],
)

win_rate = Gauge(
    "trading_win_rate",
    "Win rate (0-1)",
    ["symbol"],
)


# === Performance Metrics ===
agent_response_time = Histogram(
    "agent_response_time_seconds",
    "Agent response time in seconds",
    ["agent", "operation"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

api_request_duration = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["endpoint", "method", "status"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

cache_hits = Counter(
    "cache_hit_total",
    "Cache hit or miss",
    ["cache", "result"],  # result: hit/miss
)

cache_hit_ratio = Gauge(
    "cache_hit_ratio",
    "Cache hit ratio (0-1)",
    ["cache"],
)


# === System Metrics ===
memory_bytes = Gauge(
    "system_memory_bytes",
    "Memory usage in bytes",
)

virtual_memory_bytes = Gauge(
    "system_virtual_memory_bytes",
    "Virtual memory usage in bytes",
)

cpu_percent = Gauge(
    "system_cpu_percent",
    "CPU usage percent (0-100)",
)

disk_usage_bytes = Gauge(
    "system_disk_usage_bytes",
    "Disk usage in bytes",
    ["path"],
)


def collect_system_metrics() -> None:
    """Collect current system metrics (call periodically)."""
    try:
        mem = psutil.virtual_memory()
        memory_bytes.set(int(mem.used))
        virtual_memory_bytes.set(int(mem.total))

        cpu_percent.set(float(psutil.cpu_percent(interval=0.1)))

        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_usage_bytes.labels(path=partition.mountpoint).set(int(usage.used))
            except (PermissionError, OSError):
                pass
    except Exception:
        pass  # Silently ignore collection errors


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to record API request duration."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Record request duration and forward response."""
        if request.url.path == "/metrics":
            return await call_next(request)

        start_time = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start_time

        # Normalize status code group
        status_group = f"{response.status_code // 100}xx"

        api_request_duration.labels(
            endpoint=request.url.path,
            method=request.method,
            status=status_group,
        ).observe(duration)

        return response
