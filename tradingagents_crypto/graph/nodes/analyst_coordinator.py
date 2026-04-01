"""
Analyst coordinator for managing parallel analyst execution.
"""
from __future__ import annotations

import asyncio
from typing import Any

from tradingagents_crypto.agents.factory import AgentFactory


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
        for task, result in zip(high_priority, high_results):
            if not isinstance(result, Exception):
                results[task["type"]] = result
            else:
                results[task["type"]] = {"error": str(result)}

    # Low priority: serial execution (fallback if high priority fails)
    if not results and low_priority:
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
