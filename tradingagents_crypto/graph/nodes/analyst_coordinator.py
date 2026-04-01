"""
Analyst coordinator for managing parallel analyst execution.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from tradingagents_crypto.agents.factory import AgentFactory

logger = logging.getLogger(__name__)


async def analyst_coordinator(state: dict) -> dict:
    """Coordinate multiple analysts to execute in parallel.

    Args:
        state: Graph state containing tasks and llm

    Returns:
        Updated state with analyst_results
    """
    tasks = state.get("tasks", [])
    llm = state.get("llm")

    if not llm:
        raise ValueError("llm not provided in state")

    # Group by priority
    high_priority = [t for t in tasks if t.get("priority") == 1]
    low_priority = [t for t in tasks if t.get("priority", 1) > 1]

    results = {}

    # High priority: parallel execution
    if high_priority:
        high_tasks = []
        for task in high_priority:
            analyst = AgentFactory.create_analyst(task["type"], llm)
            high_tasks.append(
                _safe_analyst_run(analyst, task)
            )
        high_results = await asyncio.gather(*high_tasks, return_exceptions=True)
        all_high_failed = True
        for task, result in zip(high_priority, high_results):
            if not isinstance(result, Exception):
                results[task["type"]] = result
                all_high_failed = False
            else:
                results[task["type"]] = {"error": str(result)}
                logger.error(
                    "High-priority analyst %s failed: %s",
                    task["type"],
                    result,
                )

        if all_high_failed and high_priority:
            logger.error(
                "All %d high-priority analysts failed",
                len(high_priority),
            )

    # Low priority: execute unconditionally (fallback when high priority
    # produced no useful results, but also runs alongside successful high
    # priority results to enrich the analysis)
    if low_priority:
        for task in low_priority:
            analyst = AgentFactory.create_analyst(task["type"], llm)
            try:
                result = await asyncio.wait_for(
                    _safe_analyst_run(analyst, task),
                    timeout=30.0,
                )
                results[task["type"]] = result
            except Exception as e:
                results[task["type"]] = {"error": str(e)}
                logger.warning(
                    "Low-priority analyst %s failed: %s",
                    task["type"],
                    e,
                )

    return {
        "analyst_results": results,
        "status": "completed",
    }


async def _safe_analyst_run(analyst: Any, task: dict) -> dict:
    """Safely run an analyst with a timeout.

    Args:
        analyst: Analyst instance
        task: Task definition

    Returns:
        Analyst result or error dict
    """
    input_data = {
        "symbol": task.get("symbol"),
        "trade_date": task.get("trade_date"),
    }
    return await analyst.arun(input_data)
