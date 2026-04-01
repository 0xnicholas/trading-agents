"""
Hyperliquid dataflows utilities.

Time conversion, retry logic, and helpers.
"""
__all__ = ['ms_to_dt', 'dt_to_ms', 'now_ms', 'calc_time_range', 'is_valid_interval', 'get_http_session', 'retry_on_rate_limit', 'http_get']
import time
import logging
import threading
from datetime import datetime, timezone
from typing import Callable, TypeVar, Any
from functools import wraps

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


def ms_to_dt(ms: int) -> datetime:
    """Convert Unix milliseconds to datetime (UTC)."""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


def dt_to_ms(dt: datetime) -> int:
    """Convert datetime to Unix milliseconds (UTC)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def now_ms() -> int:
    """Get current time in Unix milliseconds."""
    return int(time.time() * 1000)


def calc_time_range(
    interval: str,
    days: int,
    end_ms: int | None = None,
) -> tuple[int, int]:
    """
    Calculate time range for HL API queries.

    Args:
        interval: "1h", "4h", or "1d"
        days: number of days to look back
        end_ms: end time in ms (default: now)

    Returns:
        (start_ms, end_ms)
    """
    if end_ms is None:
        end_ms = now_ms()

    hour_ms = 3600 * 1000
    day_ms = 24 * hour_ms

    if interval == "1h":
        start_ms = end_ms - days * day_ms
    elif interval == "4h":
        # 6 four-hour periods per day
        start_ms = end_ms - days * 6 * hour_ms
    elif interval == "1d":
        start_ms = end_ms - days * day_ms
    else:
        raise ValueError(f"Unknown interval: {interval}")

    return start_ms, end_ms


def is_valid_interval(interval: str) -> bool:
    """Check if interval is valid."""
    return interval in ("1h", "4h", "1d")


# HTTP client with thread-local session for connection pooling
_thread_local = threading.local()


def get_http_session() -> requests.Session:
    """Get or create a thread-local HTTP session for thread safety."""
    if not hasattr(_thread_local, "session") or _thread_local.session is None:
        _thread_local.session = requests.Session()
        _thread_local.session.headers.update(
            {"Content-Type": "application/json"}
        )
    return _thread_local.session


# Rate limit retry decorator
def retry_on_rate_limit(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
):
    """Decorator to retry on rate limit (429) or timeout."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(min=min_wait, max=max_wait),
        retry=retry_if_exception_type((requests.Timeout, requests.HTTPError)),
        reraise=True,
    )


@retry_on_rate_limit()
def http_get(url: str, **kwargs) -> requests.Response:
    """HTTP GET with retry and connection pooling."""
    session = get_http_session()
    response = session.get(url, timeout=10, **kwargs)
    response.raise_for_status()
    return response
