"""
Alert rules engine for monitoring trading system health.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Awaitable

from tradingagents_crypto.alerts.webhook import WebhookClient


# Type alias for alert check functions
AlertCheckFn = Callable[[], Awaitable["Alert | None"]]


@dataclass
class AlertRule:
    """Alert rule definition."""
    name: str
    check_fn: AlertCheckFn
    cooldown_seconds: int = 60


@dataclass
class Alert:
    """Alert instance."""
    level: str
    title: str
    message: str
    context: dict = field(default_factory=dict)


class AlertEngine:
    """Alert rules engine with cooldown management."""

    def __init__(
        self,
        webhook_client: WebhookClient,
        config,  # AlertConfig
    ):
        self.webhook = webhook_client
        self.config = config
        self._rules: list[AlertRule] = []
        self._last_alert_time: dict[str, datetime] = {}

        # Register default rules
        self._register_default_rules()

    def _register_default_rules(self):
        """Register default alert rules."""
        self.add_rule(AlertRule(
            name="consecutive_loss",
            check_fn=self._check_consecutive_loss,
            cooldown_seconds=self.config.alert_cooldown_seconds,
        ))
        self.add_rule(AlertRule(
            name="api_error_rate",
            check_fn=self._check_api_error_rate,
            cooldown_seconds=self.config.alert_cooldown_seconds,
        ))
        self.add_rule(AlertRule(
            name="agent_timeout",
            check_fn=self._check_agent_timeout,
            cooldown_seconds=self.config.alert_cooldown_seconds,
        ))
        self.add_rule(AlertRule(
            name="cache_hit_low",
            check_fn=self._check_cache_hit_low,
            cooldown_seconds=300,
        ))

    def add_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self._rules.append(rule)

    async def check_all(self):
        """Execute all rule checks."""
        for rule in self._rules:
            if self._is_in_cooldown(rule.name):
                continue
            alert = await rule.check_fn()
            if alert:
                await self._send_alert(rule.name, alert)

    def _is_in_cooldown(self, rule_name: str) -> bool:
        last = self._last_alert_time.get(rule_name)
        if not last:
            return False
        elapsed = (datetime.now(timezone.utc) - last).total_seconds()
        rule = next((r for r in self._rules if r.name == rule_name), None)
        return elapsed < (rule.cooldown_seconds if rule else 60)

    async def _send_alert(self, rule_name: str, alert: Alert):
        """Send an alert via webhook."""
        self._last_alert_time[rule_name] = datetime.now(timezone.utc)
        await self.webhook.send(
            level=alert.level,
            title=alert.title,
            message=alert.message,
            context=alert.context,
        )

    # === Built-in check functions ===

    async def _check_consecutive_loss(self) -> Alert | None:
        """Check for consecutive losses."""
        recent_losses = self._get_recent_losses(
            self.config.consecutive_loss_threshold
        )
        if len(recent_losses) < self.config.consecutive_loss_threshold:
            return None

        total_loss = sum(recent_losses)
        if abs(total_loss) > self.config.consecutive_loss_pct_threshold:
            return Alert(
                level="HIGH",
                title="连续亏损告警",
                message=(
                    f"检测到 {len(recent_losses)} 笔连续亏损，"
                    f"总亏损 {total_loss * 100:.1f}%"
                ),
                context={
                    "consecutive_losses": len(recent_losses),
                    "total_loss_pct": total_loss,
                    "recent_losses": recent_losses,
                },
            )
        return None

    async def _check_api_error_rate(self) -> Alert | None:
        """Check API error rate."""
        # This would be implemented with actual metrics tracking
        return None

    async def _check_agent_timeout(self) -> Alert | None:
        """Check for agent timeouts."""
        # This would be implemented with actual timing metrics
        return None

    async def _check_cache_hit_low(self) -> Alert | None:
        """Check for low cache hit ratio."""
        # This would be implemented with actual cache metrics
        return None

    def _get_recent_losses(self, count: int) -> list[float]:
        """Get recent losing trades for analysis."""
        # In production, this would read from metrics or trade history
        return []
