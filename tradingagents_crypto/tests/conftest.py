"""
Pytest configuration and shared fixtures.
"""
import sys
import pytest
from pathlib import Path

# Add project root and src/ to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


@pytest.fixture(autouse=True)
def clean_agent_registry():
    """Automatically clean agent registry before each test."""
    from tradingagents_crypto.agents.registry import AgentRegistry
    AgentRegistry.clear()
    yield
    AgentRegistry.clear()
