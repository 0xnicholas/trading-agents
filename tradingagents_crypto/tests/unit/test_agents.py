"""
Unit tests for agent base classes and schemas.
"""
import pytest
from unittest.mock import MagicMock, patch

from agents.base import (
    AgentConfig,
    CryptoAgentBase,
    AnalystReport,
    TradingDecision,
)


class TestAgentConfig:
    """Tests for AgentConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = AgentConfig()
        assert config.model_name == "gpt-4o"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.timeout_seconds == 60

    def test_custom_config(self):
        """Test custom configuration."""
        config = AgentConfig(
            model_name="gpt-4o-mini",
            temperature=0.5,
            max_tokens=2048,
        )
        assert config.model_name == "gpt-4o-mini"
        assert config.temperature == 0.5
        assert config.max_tokens == 2048


class TestCryptoAgentBase:
    """Tests for CryptoAgentBase."""

    def test_agent_creation(self):
        """Test agent can be created with basic params."""
        agent = CryptoAgentBase(
            name="TestAgent",
            description="A test agent",
            tools=[],
        )
        assert agent.name == "TestAgent"
        assert agent.description == "A test agent"
        assert len(agent.tools) == 0

    def test_agent_with_tools(self):
        """Test agent with tools."""
        tool1 = MagicMock()
        tool1.name = "tool1"
        tool2 = MagicMock()
        tool2.name = "tool2"

        agent = CryptoAgentBase(
            name="ToolAgent",
            description="An agent with tools",
            tools=[tool1, tool2],
        )
        assert len(agent.tools) == 2

    def test_build_system_prompt(self):
        """Test system prompt generation."""
        agent = CryptoAgentBase(
            name="TestAgent",
            description="A test agent",
            tools=[],
        )
        prompt = agent.build_system_prompt()
        assert "TestAgent" in prompt
        assert "test agent" in prompt

    def test_build_system_prompt_with_extra(self):
        """Test system prompt with extra context."""
        agent = CryptoAgentBase(
            name="TestAgent",
            description="A test agent",
            tools=[],
        )
        prompt = agent.build_system_prompt("Consider BTC markets.")
        assert "BTC markets" in prompt

    def test_repr(self):
        """Test string representation."""
        agent = CryptoAgentBase(
            name="TestAgent",
            description="A test agent",
            tools=[],
        )
        assert "TestAgent" in repr(agent)
        assert "tools=0" in repr(agent)


class TestAnalystReport:
    """Tests for AnalystReport."""

    def test_create_report(self):
        """Test creating an analyst report."""
        report = AnalystReport(
            summary="BTC looks bullish",
            direction="bullish",
            confidence=0.75,
            signals={"rsi": 70, "macd": "bullish"},
            metrics={"price": 67000},
            narrative="Detailed analysis...",
        )
        assert report.summary == "BTC looks bullish"
        assert report.direction == "bullish"
        assert report.confidence == 0.75

    def test_to_dict(self):
        """Test converting report to dict."""
        report = AnalystReport(
            summary="Test",
            direction="neutral",
            confidence=0.5,
            signals={},
            metrics={},
            narrative="Test narrative",
        )
        d = report.to_dict()
        assert isinstance(d, dict)
        assert d["summary"] == "Test"
        assert d["direction"] == "neutral"
        assert d["confidence"] == 0.5


class TestTradingDecision:
    """Tests for TradingDecision."""

    def test_create_decision(self):
        """Test creating a trading decision."""
        decision = TradingDecision(
            action="long",
            size_pct=0.5,
            leverage=10,
            reason="Strong bullish signal",
        )
        assert decision.action == "long"
        assert decision.size_pct == 0.5
        assert decision.leverage == 10

    def test_decision_with_warnings(self):
        """Test decision with risk warnings."""
        decision = TradingDecision(
            action="short",
            size_pct=0.3,
            leverage=5,
            reason="Funding rate extreme",
            risk_warnings=["High volatility", "OI contracting"],
        )
        assert len(decision.risk_warnings) == 2

    def test_to_dict(self):
        """Test converting decision to dict."""
        decision = TradingDecision(
            action="hold",
            size_pct=0.0,
            leverage=1,
            reason="Uncertain market",
        )
        d = decision.to_dict()
        assert isinstance(d, dict)
        assert d["action"] == "hold"
        assert d["size_pct"] == 0.0

    def test_hold_decision(self):
        """Test hold decision has zero size."""
        decision = TradingDecision(
            action="hold",
            size_pct=0.0,
            leverage=1,
            reason="Low confidence",
        )
        assert decision.size_pct == 0.0
