"""
Meta-Agent for task decomposition and coordination.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Subtask definition."""
    type: str  # btc_analysis, eth_analysis, sol_analysis, macro_analysis
    priority: int  # 1=high, 2=medium, 3=low
    symbol: str | None = None


# Keywords that indicate which analysts are needed
_TASK_KEYWORDS = {
    "btc_analysis": ["btc", "bitcoin", "₿"],
    "eth_analysis": ["eth", "ethereum", "ether"],
    "sol_analysis": ["sol", "solana"],
    "macro_analysis": ["macro", "market", "economy", "global", "funding", "sentiment"],
}


def _infer_needed_analysts(user_request: str) -> dict[str, int]:
    """Infer which analysts are needed based on the user request.

    Args:
        user_request: The user's request text

    Returns:
        Dict mapping analyst type to priority
    """
    request_lower = user_request.lower()
    priorities: dict[str, int] = {}

    # Check each analyst type for keyword matches
    for analyst_type, keywords in _TASK_KEYWORDS.items():
        if any(kw in request_lower for kw in keywords):
            # Default priority mapping: btc/eth/macro = 1, sol = 2
            priorities[analyst_type] = 1 if analyst_type != "sol_analysis" else 2

    # Always include BTC and ETH at minimum
    if "btc_analysis" not in priorities:
        priorities["btc_analysis"] = 1
    if "eth_analysis" not in priorities:
        priorities["eth_analysis"] = 1
    if "macro_analysis" not in priorities:
        priorities["macro_analysis"] = 1

    return priorities


async def meta_agent_node(state: dict) -> dict:
    """Meta-Agent node: decompose user request into tasks.

    Uses the user_request field to dynamically determine which analysts
    to invoke and their priorities.

    Args:
        state: Graph state containing user_request and symbol

    Returns:
        Updated state with tasks list
    """
    user_request = state.get("user_request", "")
    symbol = state.get("symbol", "BTC")

    # Dynamically infer which analysts are needed based on user request
    needed = _infer_needed_analysts(user_request)

    # Build tasks from inferred needs
    tasks = []
    for analyst_type, priority in needed.items():
        if analyst_type == "macro_analysis":
            tasks.append(Task(type=analyst_type, priority=priority, symbol=None))
        else:
            tasks.append(Task(type=analyst_type, priority=priority, symbol=symbol))

    logger.info(
        "meta_agent decomposed request into %d tasks: %s",
        len(tasks),
        [t.type for t in tasks],
    )

    return {
        "tasks": [t.__dict__ for t in tasks],
        "status": "dispatched",
        "analyst_results": {},
    }
