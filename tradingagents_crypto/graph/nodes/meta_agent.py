"""
Meta-Agent for task decomposition and coordination.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class Task:
    """Subtask definition."""
    type: str  # btc_analysis, eth_analysis, sol_analysis, macro_analysis
    priority: int  # 1=high, 2=medium, 3=low
    symbol: str | None = None


async def meta_agent_node(state: dict) -> dict:
    """Meta-Agent node: decompose user request into tasks.

    Args:
        state: Graph state containing user_request and symbol

    Returns:
        Updated state with tasks list
    """
    user_request = state.get("user_request", "")
    symbol = state.get("symbol", "BTC")

    # Task decomposition strategy
    tasks = [
        Task(type="btc_analysis", priority=1, symbol=symbol),
        Task(type="eth_analysis", priority=1, symbol=symbol),
        Task(type="sol_analysis", priority=2, symbol=symbol),
        Task(type="macro_analysis", priority=1),
    ]

    return {
        "tasks": [t.__dict__ for t in tasks],
        "status": "dispatched",
        "analyst_results": {},
    }
