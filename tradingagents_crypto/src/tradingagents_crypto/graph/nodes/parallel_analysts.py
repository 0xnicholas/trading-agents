"""
Parallel analyst execution utilities.
"""
from __future__ import annotations

import asyncio
from typing import Any, Sequence


async def run_analysts_parallel(
    analysts: list,
    input_data: dict,
    timeout: float = 30.0,
) -> list[dict]:
    """Execute multiple analysts in parallel.

    Args:
        analysts: List of analyst instances
        input_data: Input data to pass to each analyst
        timeout: Timeout in seconds per analyst

    Returns:
        List of results (in same order as input analysts)
        Exceptions are converted to error dicts
    """
    tasks = []
    for analyst in analysts:
        task = asyncio.create_task(
            asyncio.wait_for(
                analyst.arun(input_data),
                timeout=timeout,
            )
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results, converting exceptions to error dicts
    processed = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            analyst_name = (
                analysts[i].config.name
                if hasattr(analysts[i], "config")
                else str(i)
            )
            processed.append({
                "error": str(result),
                "analyst": analyst_name,
            })
        else:
            processed.append(result)

    return processed


class SyncAnalystAdapter:
    """Adapter to make sync analysts work with async interface.

    Provides backwards compatibility for sync-only analysts.
    """

    def __init__(self, sync_analyst):
        self._analyst = sync_analyst

    async def arun(self, input_data: dict) -> dict:
        """Run the sync analyst in a thread pool."""
        return await asyncio.to_thread(self._analyst.run, input_data)
