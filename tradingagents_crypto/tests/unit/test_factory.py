"""
Unit tests for agent factory and registry.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from tradingagents_crypto.agents.base import BaseAgent, AgentConfig
from tradingagents_crypto.agents.factory import AgentFactory
from tradingagents_crypto.agents.registry import AgentRegistry


class MockAgent(BaseAgent):
    """Mock agent for testing."""

    async def arun(self, input_data: dict) -> dict:
        return {"result": "ok", "name": self.config.name}


class TestAgentRegistry:
    """Tests for AgentRegistry."""

    def setup_method(self):
        """Clear registry before each test."""
        AgentRegistry.clear()

    def test_register_analyst(self):
        """Test registering an analyst."""

        @AgentRegistry.register_analyst("test_analyst")
        class TestAnalyst(BaseAgent):
            async def arun(self, input_data: dict) -> dict:
                return {}

        assert "test_analyst" in AgentRegistry.list_analysts()
        assert AgentRegistry.get_analyst("test_analyst") == TestAnalyst

    def test_register_trader(self):
        """Test registering a trader."""

        @AgentRegistry.register_trader("test_trader")
        class TestTrader(BaseAgent):
            async def arun(self, input_data: dict) -> dict:
                return {}

        assert "test_trader" in AgentRegistry.list_traders()
        assert AgentRegistry.get_trader("test_trader") == TestTrader

    def test_get_analyst_not_found(self):
        """Test getting a non-existent analyst returns None."""
        result = AgentRegistry.get_analyst("nonexistent")
        assert result is None

    def test_get_trader_not_found(self):
        """Test getting a non-existent trader returns None."""
        result = AgentRegistry.get_trader("nonexistent")
        assert result is None

    def test_list_analysts_empty(self):
        """Test listing analysts when none registered."""
        AgentRegistry.clear()
        assert AgentRegistry.list_analysts() == []

    def test_list_traders_empty(self):
        """Test listing traders when none registered."""
        AgentRegistry.clear()
        assert AgentRegistry.list_traders() == []

    def test_clear(self):
        """Test clearing the registry."""
        @AgentRegistry.register_analyst("temp")
        class TempAnalyst(BaseAgent):
            async def arun(self, input_data: dict) -> dict:
                return {}

        AgentRegistry.clear()
        assert "temp" not in AgentRegistry.list_analysts()


class TestAgentFactory:
    """Tests for AgentFactory."""

    def setup_method(self):
        """Clear and set up registry before each test."""
        AgentRegistry.clear()
        # Register a mock analyst and trader
        AgentRegistry._analysts["test_analyst"] = MockAgent
        AgentRegistry._traders["test_trader"] = MockAgent

    def test_create_analyst_with_default_config(self):
        """Test creating an analyst with default config."""
        llm = MagicMock()
        agent = AgentFactory.create_analyst("test_analyst", llm)

        assert isinstance(agent, MockAgent)
        assert agent.config.name == "test_analyst"
        assert agent.llm is llm

    def test_create_analyst_with_custom_config(self):
        """Test creating an analyst with custom config."""
        llm = MagicMock()
        config = AgentConfig(name="custom", model="gpt-4o-mini")
        agent = AgentFactory.create_analyst("test_analyst", llm, config)

        assert isinstance(agent, MockAgent)
        assert agent.config.name == "custom"

    def test_create_trader_with_default_config(self):
        """Test creating a trader with default config."""
        llm = MagicMock()
        agent = AgentFactory.create_trader("test_trader", llm)

        assert isinstance(agent, MockAgent)
        assert agent.config.name == "test_trader"
        assert agent.llm is llm

    def test_unknown_analyst_raises(self):
        """Test that unknown analyst type raises ValueError."""
        llm = MagicMock()
        with pytest.raises(ValueError, match="Unknown analyst type"):
            AgentFactory.create_analyst("unknown", llm)

    def test_unknown_trader_raises(self):
        """Test that unknown trader type raises ValueError."""
        llm = MagicMock()
        with pytest.raises(ValueError, match="Unknown trader type"):
            AgentFactory.create_trader("unknown", llm)

    def test_error_message_lists_available(self):
        """Test that error message lists available agent types."""
        llm = MagicMock()
        try:
            AgentFactory.create_analyst("unknown", llm)
        except ValueError as e:
            assert "Available:" in str(e)
            assert "test_analyst" in str(e)

    @pytest.mark.asyncio
    async def test_mock_agent_arun(self):
        """Test that mock agent arun works."""
        llm = MagicMock()
        config = AgentConfig(name="test")
        agent = MockAgent(config=config, llm=llm)
        result = await agent.arun({"symbol": "BTC"})

        assert result["result"] == "ok"
        assert result["name"] == "test"
