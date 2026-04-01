"""
Prometheus metrics definitions for trading system.

Provides counters, gauges, and histograms for trading, performance, and system metrics.
"""
from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Response


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
    ["endpoint", "status"],
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

cpu_percent = Gauge(
    "system_cpu_percent",
    "CPU usage percent (0-100)",
)


# === FastAPI app for metrics endpoint ===
app = FastAPI()


@app.get("/metrics")
def metrics():
    """Prometheus metrics scrape endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
