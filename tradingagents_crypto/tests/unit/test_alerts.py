"""
Unit tests for alert system.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tradingagents_crypto.alerts.webhook import WebhookClient
from tradingagents_crypto.alerts.rules import AlertEngine, AlertRule, Alert


class TestWebhookClient:
    """Tests for WebhookClient."""

    @pytest.fixture
    def client(self):
        """Create a WebhookClient with mocked HTTP."""
        return WebhookClient(discord_url="https://discord.com/webhook/test")

    @pytest.mark.asyncio
    async def test_send_discord(self, client):
        """Test sending Discord webhook."""
        client._http = AsyncMock()
        result = await client.send("HIGH", "Test Alert", "Test message")
        assert result is True
        client._http.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_with_context(self, client):
        """Test sending alert with context."""
        client._http = AsyncMock()
        result = await client.send(
            "MEDIUM",
            "Test",
            "Message",
            context={"symbol": "BTC", "size": 1000},
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_send_no_webhook(self):
        """Test sending when no webhook configured."""
        client = WebhookClient(discord_url=None, slack_url=None)
        result = await client.send("LOW", "Test", "Message")
        assert result is False

    @pytest.mark.asyncio
    async def test_discord_failure_returns_false(self, client):
        """Test that Discord failure returns False."""
        client._http = AsyncMock()
        client._http.post.side_effect = Exception("Network error")
        result = await client.send("HIGH", "Test", "Message")
        assert result is False

    @pytest.mark.asyncio
    async def test_slack_webhook(self):
        """Test Slack webhook integration."""
        client = WebhookClient(slack_url="https://slack.com/webhook/test")
        client._http = AsyncMock()
        result = await client.send("HIGH", "Test", "Message")
        assert result is True

    @pytest.mark.asyncio
    async def test_close(self, client):
        """Test closing HTTP client."""
        client._http = AsyncMock()
        await client.close()
        client._http.aclose.assert_called_once()


class TestAlertRule:
    """Tests for AlertRule dataclass."""

    def test_alert_rule_creation(self):
        """Test creating an AlertRule."""
        async def dummy_check():
            return None

        rule = AlertRule(
            name="test_rule",
            check_fn=dummy_check,
            cooldown_seconds=120,
        )
        assert rule.name == "test_rule"
        assert rule.cooldown_seconds == 120


class TestAlert:
    """Tests for Alert dataclass."""

    def test_alert_creation(self):
        """Test creating an Alert."""
        alert = Alert(
            level="HIGH",
            title="Test Alert",
            message="Test message",
            context={"key": "value"},
        )
        assert alert.level == "HIGH"
        assert alert.title == "Test Alert"
        assert alert.context["key"] == "value"

    def test_alert_default_context(self):
        """Test Alert with default empty context."""
        alert = Alert(level="LOW", title="T", message="M")
        assert alert.context == {}


class TestAlertEngine:
    """Tests for AlertEngine."""

    @pytest.fixture
    def mock_webhook(self):
        """Create a mock WebhookClient."""
        webhook = AsyncMock()
        webhook.send = AsyncMock(return_value=True)
        return webhook

    @pytest.fixture
    def mock_config(self):
        """Create a mock AlertConfig."""
        config = MagicMock()
        config.alert_cooldown_seconds = 60
        config.consecutive_loss_threshold = 5
        config.consecutive_loss_pct_threshold = 0.10
        config.api_error_rate_threshold = 0.10
        config.api_error_window_minutes = 5
        config.agent_timeout_seconds = 30.0
        config.cache_hit_ratio_threshold = 0.50
        config.disk_space_threshold_gb = 1.0
        return config

    @pytest.fixture
    def engine(self, mock_webhook, mock_config):
        """Create an AlertEngine with mocks."""
        return AlertEngine(mock_webhook, mock_config)

    def test_add_rule(self, engine):
        """Test adding a rule to the engine."""
        initial_count = len(engine._rules)

        async def dummy_check():
            return None

        engine.add_rule(AlertRule(name="test", check_fn=dummy_check))
        assert len(engine._rules) == initial_count + 1

    @pytest.mark.asyncio
    async def test_check_all_no_alerts(self, engine):
        """Test check_all when no alerts triggered."""
        # All default checks return None
        await engine.check_all()
        # No alerts should be sent
        engine.webhook.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_cooldown_prevents_duplicate(self, engine):
        """Test that cooldown prevents duplicate alerts."""
        # Set last alert time to now
        from datetime import datetime, timezone
        engine._last_alert_time["consecutive_loss"] = datetime.now(timezone.utc)

        # Should skip due to cooldown
        await engine.check_all()
        engine.webhook.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_custom_rule_execution(self, engine, mock_webhook):
        """Test custom rule is executed and can send alerts."""
        alert_sent = []

        async def custom_check():
            return Alert(
                level="HIGH",
                title="Custom Alert",
                message="Custom message",
            )

        engine.add_rule(AlertRule(
            name="custom",
            check_fn=custom_check,
            cooldown_seconds=0,  # No cooldown for test
        ))

        await engine.check_all()
        # Should have sent the custom alert
        assert mock_webhook.send.called

    @pytest.mark.asyncio
    async def test_alert_sent_with_correct_level(self, engine, mock_webhook):
        """Test that alert is sent with correct level."""

        async def high_alert_check():
            return Alert(
                level="CRITICAL",
                title="Critical",
                message="Critical message",
            )

        engine.add_rule(AlertRule(
            name="critical",
            check_fn=high_alert_check,
            cooldown_seconds=0,
        ))

        await engine.check_all()
        mock_webhook.send.assert_called_once()
        call_args = mock_webhook.send.call_args
        assert call_args[1]["level"] == "CRITICAL"

    def test_get_recent_losses_default_empty(self, engine):
        """Test that _get_recent_losses returns empty list by default."""
        losses = engine._get_recent_losses(5)
        assert losses == []

    def test_multiple_rules_registered(self, engine):
        """Test that multiple rules are registered by default."""
        rule_names = [r.name for r in engine._rules]
        assert "consecutive_loss" in rule_names
        assert "api_error_rate" in rule_names
        assert "agent_timeout" in rule_names
        assert "cache_hit_low" in rule_names
