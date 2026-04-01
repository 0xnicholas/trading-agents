"""
Shared memory for multi-agent coordination.
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SharedState:
    """Multi-agent shared state."""
    symbol: str
    trade_date: str

    # Analysis results
    btc_signal: dict | None = None
    eth_signal: dict | None = None
    sol_signal: dict | None = None
    macro_signal: dict | None = None

    # Decisions
    risk_assessment: dict | None = None
    trading_decision: dict | None = None
    final_decision: str = "hold"

    # Metadata
    trace_id: str = ""
    messages: list = field(default_factory=list)


class SharedMemory:
    """Thread-safe shared memory with optional Redis persistence."""

    def __init__(self, use_redis: bool = False, redis_url: str | None = None):
        self._lock = asyncio.Lock()
        self._data: dict[str, SharedState] = {}
        self._use_redis = use_redis
        self._redis_url = redis_url
        self._redis = None

    async def initialize(self):
        """Initialize async resources (e.g., Redis connection)."""
        if self._use_redis:
            import redis.asyncio as redis
            self._redis = redis.from_url(
                self._redis_url or "redis://localhost:6379"
            )

    async def read(self, trace_id: str) -> SharedState | None:
        """Read state for a trace ID.

        Args:
            trace_id: Unique trace identifier

        Returns:
            SharedState if found, None otherwise
        """
        async with self._lock:
            return self._data.get(trace_id)

    async def write(self, trace_id: str, state: SharedState):
        """Write state for a trace ID.

        Args:
            trace_id: Unique trace identifier
            state: SharedState to store
        """
        async with self._lock:
            self._data[trace_id] = state
            if self._redis:
                await self._redis.set(
                    f"state:{trace_id}",
                    json.dumps(self._to_dict(state)),
                    ex=3600,
                )

    async def update(self, trace_id: str, **kwargs):
        """Update specific fields in a state.

        Args:
            trace_id: Unique trace identifier
            **kwargs: Fields to update
        """
        async with self._lock:
            if trace_id not in self._data:
                raise KeyError(f"No state found for trace_id: {trace_id}")
            state = self._data[trace_id]
            for key, value in kwargs.items():
                if hasattr(state, key):
                    setattr(state, key, value)
                else:
                    raise ValueError(f"Unknown field: {key}")

    async def delete(self, trace_id: str):
        """Delete state for a trace ID."""
        async with self._lock:
            if trace_id in self._data:
                del self._data[trace_id]
            if self._redis:
                await self._redis.delete(f"state:{trace_id}")

    def _to_dict(self, state: SharedState) -> dict:
        """Convert SharedState to dict for JSON serialization."""
        return {
            "symbol": state.symbol,
            "trade_date": state.trade_date,
            "btc_signal": state.btc_signal,
            "eth_signal": state.eth_signal,
            "sol_signal": state.sol_signal,
            "macro_signal": state.macro_signal,
            "risk_assessment": state.risk_assessment,
            "trading_decision": state.trading_decision,
            "final_decision": state.final_decision,
            "trace_id": state.trace_id,
            "messages": state.messages,
        }

    @classmethod
    def from_dict(cls, data: dict) -> SharedState:
        """Create SharedState from dict."""
        return SharedState(
            symbol=data.get("symbol", ""),
            trade_date=data.get("trade_date", ""),
            btc_signal=data.get("btc_signal"),
            eth_signal=data.get("eth_signal"),
            sol_signal=data.get("sol_signal"),
            macro_signal=data.get("macro_signal"),
            risk_assessment=data.get("risk_assessment"),
            trading_decision=data.get("trading_decision"),
            final_decision=data.get("final_decision", "hold"),
            trace_id=data.get("trace_id", ""),
            messages=data.get("messages", []),
        )
