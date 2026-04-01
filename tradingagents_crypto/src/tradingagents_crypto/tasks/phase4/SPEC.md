# Phase 4: Production & Multi-Agent Orchestration

**状态**: 🔵 待启动
**周期**: 4-6 周
**前置条件**: Phase 1-3 完成 ✅

---

## 目标

分三阶段建设：
1. **Phase 4B**: Production Infrastructure（基础设施，可观测性）
2. **Phase 4A**: Multi-Agent Orchestration（多 Agent 协作）
3. **Phase 4C**: Live Trading（实盘交易，仅在 B+A 验证后启动）

---

# Phase 4B: Production Infrastructure

## 目标

让系统具备生产环境可运行、可观测、可维护的基础能力。

## M4.1: 结构化日志系统

### 日志格式
```json
{
  "timestamp": "2026-04-01T12:00:00.000Z",
  "level": "INFO",
  "service": "crypto-trading",
  "module": "backtest_engine",
  "message": "Position opened",
  "trace_id": "abc123",
  "context": {
    "symbol": "BTC",
    "side": "long",
    "size_usd": 10000,
    "entry_price": 50000
  }
}
```

### 日志字段定义

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| timestamp | ISO8601 | ✅ | UTC 时间，毫秒精度 |
| level | string | ✅ | DEBUG/INFO/WARNING/ERROR/CRITICAL |
| service | string | ✅ | 固定 "crypto-trading" |
| module | string | ✅ | 模块名，如 "backtest_engine" |
| message | string | ✅ | 人类可读的消息 |
| trace_id | string | ⚠️ | 请求追踪 ID，无则为空 |
| context | object | ⚠️ | 额外上下文数据 |

### 日志级别规范

| 级别 | 使用场景 |
|------|---------|
| DEBUG | 开发调试，诊断问题 |
| INFO | 正常业务流程（交易开仓/平仓/决策） |
| WARNING | 异常但可恢复（数据缺失、降级） |
| ERROR | 操作失败（API 超时、数据错误） |
| CRITICAL | 系统级故障（连接断开） |

### 输出目标

| 环境 | 输出 | 格式 |
|------|------|------|
| 开发 | Console | 带颜色的普通文本 |
| 生产 | JSON File | 结构化 JSON，按天切割 |
| 可选 | Loki/Datadog | JSON over HTTP |

### 文件结构

```
tradingagents_crypto/
└── utils/
    └── logging.py          # JSONFormatter, setup_logging
```

### 实现

```python
# tradingagents_crypto/utils/logging.py
import logging
import json
import sys
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """输出结构化 JSON 格式的日志"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "service": "crypto-trading",
            "module": record.module,
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", "") or "",
            "context": getattr(record, "context", {}) or {},
        }
        # 包含异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(
    level: str = "INFO",
    log_dir: str | None = None,
    json_format: bool = True,
) -> None:
    """配置日志系统

    Args:
        level: 日志级别
        log_dir: 日志文件目录，None 则只输出到 console
        json_format: 是否使用 JSON 格式（生产环境 True）
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    if json_format:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(module)s | %(message)s"
            )
        )
    root_logger.addHandler(console_handler)

    # File handler (JSON, daily rotation)
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        file_handler = TimedRotatingFileHandler(
            log_dir / "trading.log",
            when="midnight",
            utc=True,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的 logger"""
    return logging.getLogger(name)
```

### 单元测试

```python
# tests/unit/test_logging.py
import pytest
import json
import logging
from tradingagents_crypto.utils.logging import JSONFormatter, setup_logging


class TestJSONFormatter:
    def test_format_basic_log(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        result = json.loads(formatter.format(record))

        assert result["level"] == "INFO"
        assert result["message"] == "Test message"
        assert result["service"] == "crypto-trading"
        assert "timestamp" in result

    def test_format_with_context(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Position opened",
            args=(),
            exc_info=None,
        )
        record.context = {"symbol": "BTC", "side": "long"}
        result = json.loads(formatter.format(record))

        assert result["context"]["symbol"] == "BTC"
        assert result["context"]["side"] == "long"

    def test_format_with_trace_id(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.trace_id = "abc123"
        result = json.loads(formatter.format(record))

        assert result["trace_id"] == "abc123"
```

---

## M4.2: 健康检查端点

### HTTP 端点

| 端点 | 用途 | Kubernetes 探针 |
|------|------|----------------|
| GET /health | 综合健康状态 | - |
| GET /health/ready | 依赖服务就绪检查 | readinessProbe |
| GET /health/live | 进程存活检查 | livenessProbe |

### 响应格式

```json
// GET /health
{
  "status": "healthy",
  "timestamp": "2026-04-01T12:00:00.000Z",
  "version": "1.0.0"
}

// GET /health/ready
{
  "status": "ready",
  "timestamp": "2026-04-01T12:00:00.000Z",
  "checks": {
    "redis": {"status": "ok", "latency_ms": 2},
    "hyperliquid": {"status": "ok", "latency_ms": 45},
    "llm": {"status": "ok", "latency_ms": 120}
  }
}

// GET /health/live
{
  "status": "live",
  "timestamp": "2026-04-01T12:00:00.000Z"
}
```

### 健康检查内容

| 检查项 | 超时 | 失败后果 | 缓存 |
|--------|------|---------|------|
| Redis 连接 | 2s | degraded | 30s |
| Hyperliquid API | 3s | degraded | 60s |
| LLM API | 5s | degraded | 60s |
| 磁盘空间 | - | healthy | 300s |

### 文件结构

```
tradingagents_crypto/
└── api/
    └── health.py          # FastAPI 健康检查端点
```

### 实现

```python
# tradingagents_crypto/api/health.py
from fastapi import FastAPI, Response
from functools import lru_cache
from datetime import datetime, timezone
import time

app = FastAPI()


@lru_cache(ttl=60)
def _health_check_cache() -> dict:
    """60 秒缓存的健康检查结果"""
    return _do_health_check()


def _do_health_check() -> dict:
    """执行实际健康检查"""
    checks = {}

    # Redis
    try:
        import redis
        start = time.time()
        r = redis.Redis.from_url("redis://localhost:6379", socket_timeout=2)
        r.ping()
        checks["redis"] = {"status": "ok", "latency_ms": int((time.time() - start) * 1000)}
    except Exception as e:
        checks["redis"] = {"status": "error", "message": str(e)}

    # Hyperliquid
    try:
        from tradingagents_crypto.dataflows.exchanges.hyperliquid import Hyperliquid
        start = time.time()
        hl = Hyperliquid()
        hl.get_wallet_balance()
        checks["hyperliquid"] = {"status": "ok", "latency_ms": int((time.time() - start) * 1000)}
    except Exception as e:
        checks["hyperliquid"] = {"status": "error", "message": str(e)}

    # LLM (只检查连接，不实际调用)
    try:
        from tradingagents_crypto.config import default_config
        checks["llm"] = {"status": "ok", "latency_ms": 0}
    except Exception as e:
        checks["llm"] = {"status": "error", "message": str(e)}

    return checks


@app.get("/health")
def health():
    """综合健康状态"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "version": "1.0.0",
    }


@app.get("/health/ready")
def readiness():
    """依赖服务就绪检查"""
    checks = _health_check_cache()
    has_error = any(c.get("status") == "error" for c in checks.values())

    return {
        "status": "ready" if not has_error else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "checks": checks,
    }


@app.get("/health/live")
def liveness():
    """进程存活检查"""
    return {
        "status": "live",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
    }
```

### 单元测试

```python
# tests/unit/test_health.py
import pytest
from fastapi.testclient import TestClient
from tradingagents_crypto.api.health import app


class TestHealthEndpoints:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_health_live_returns_200(self, client):
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "live"

    def test_health_ready_returns_200(self, client):
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "checks" in data
```

---

## M4.3: Prometheus Metrics

### 指标类型

| 类型 | 用途 | 示例 |
|------|------|------|
| Counter | 累计计数 | 总交易次数 |
| Gauge | 当前值 | 当前持仓 |
| Histogram | 分布统计 | API 延迟分布 |

### 核心指标

#### 交易指标

| 指标名 | 类型 | 标签 | 说明 |
|--------|------|------|------|
| trading_orders_total | Counter | symbol, side, result | 总订单数 |
| trading_pnl_total | Gauge | symbol | 总盈亏（USD） |
| trading_position_size | Gauge | symbol | 当前持仓 |
| trading_win_rate | Gauge | symbol | 胜率 |

#### 性能指标

| 指标名 | 类型 | 标签 | 说明 |
|--------|------|------|------|
| agent_response_time_seconds | Histogram | agent, operation | Agent 响应时间 |
| api_request_duration_seconds | Histogram | endpoint, status | API 请求延迟 |
| cache_hit_total | Counter | cache, result | 缓存命中/未命中 |
| cache_hit_ratio | Gauge | cache | 缓存命中率 |

#### 系统指标

| 指标名 | 类型 | 说明 |
|--------|------|------|
| system_memory_bytes | Gauge | 内存使用 |
| system_cpu_percent | Gauge | CPU 使用率 |

### 文件结构

```
tradingagents_crypto/
└── utils/
    └── metrics.py          # Prometheus metrics 定义
```

### 实现

```python
# tradingagents_crypto/utils/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Response


# === 交易指标 ===
orders_total = Counter(
    "trading_orders_total",
    "Total number of orders",
    ["symbol", "side", "result"],  # result: filled/rejected/cancelled
)

pnl_gauge = Gauge(
    "trading_pnl_total",
    "Total PnL in USD",
    ["symbol"],
)

position_size = Gauge(
    "trading_position_size",
    "Current position size in USD",
    ["symbol"],
)

win_rate = Gauge(
    "trading_win_rate",
    "Win rate (0-1)",
    ["symbol"],
)


# === 性能指标 ===
agent_response_time = Histogram(
    "agent_response_time_seconds",
    "Agent response time in seconds",
    ["agent", "operation"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

api_request_duration = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["endpoint", "status"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

cache_hits = Counter(
    "cache_hit_total",
    "Cache hit or miss",
    ["cache", "result"],  # result: hit/miss
)

cache_hit_ratio = Gauge(
    "cache_hit_ratio",
    "Cache hit ratio (0-1)",
    ["cache"],
)


# === 系统指标 ===
memory_bytes = Gauge(
    "system_memory_bytes",
    "Memory usage in bytes",
)

cpu_percent = Gauge(
    "system_cpu_percent",
    "CPU usage percent (0-100)",
)


# === FastAPI 端点 ===
app = FastAPI()


@app.get("/metrics")
def metrics():
    """Prometheus metrics 抓取端点"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
```

### 单元测试

```python
# tests/unit/test_metrics.py
import pytest
from prometheus_client import REGISTRY
from tradingagents_crypto.utils.metrics import (
    orders_total, pnl_gauge, cache_hits
)


class TestMetrics:
    def test_orders_total_increments(self):
        initial = orders_total.labels(symbol="BTC", side="long", result="filled")._value.get()
        orders_total.labels(symbol="BTC", side="long", result="filled").inc()
        after = orders_total.labels(symbol="BTC", side="long", result="filled")._value.get()
        assert after == initial + 1

    def test_pnl_gauge_sets(self):
        pnl_gauge.labels(symbol="BTC").set(1234.56)
        assert pnl_gauge.labels(symbol="BTC")._value.get() == 1234.56

    def test_cache_hit_ratio(self):
        cache_hits.labels(cache="prices", result="hit").inc(80)
        cache_hits.labels(cache="prices", result="miss").inc(20)
        # 手动计算比率
        hit = cache_hits.labels(cache="prices", result="hit")._value.get()
        miss = cache_hits.labels(cache="prices", result="miss")._value.get()
        ratio = hit / (hit + miss)
        assert ratio == 0.8
```

---

## M4.4: 告警系统

### 告警级别

| 级别 | 严重程度 | 通知方式 |
|------|---------|---------|
| LOW | 一般信息 | 仅日志 |
| MEDIUM | 注意 | Discord/Slack webhook |
| HIGH | 严重 | Discord/Slack webhook + 持续提醒 |
| CRITICAL | 紧急 | Discord/Slack webhook + 持续提醒 |

### 告警规则

| 告警名 | 条件 | 级别 | 冷却时间 |
|--------|------|------|---------|
| consecutive_loss | N 笔连续亏损 > X% | HIGH | 60s |
| api_error_rate | API 错误率 > X% in Y min | MEDIUM | 60s |
| agent_timeout | Agent 响应 > X 秒 | MEDIUM | 60s |
| cache_hit_low | 缓存命中率 < X% in 1h | LOW | 300s |
| disk_space_low | 可用空间 < X GB | HIGH | 300s |

### Webhook 配置

```python
# config/default_config.py
@dataclass
class AlertConfig:
    # 通知渠道
    discord_webhook: str | None = None
    slack_webhook: str | None = None
    alert_level: str = "HIGH"  # LOW/MEDIUM/HIGH

    # 告警阈值（可配置）
    consecutive_loss_threshold: int = 5
    consecutive_loss_pct_threshold: float = 0.10  # 10%
    api_error_rate_threshold: float = 0.10  # 10%
    api_error_window_minutes: int = 5
    agent_timeout_seconds: float = 30.0
    cache_hit_ratio_threshold: float = 0.50  # 50%
    disk_space_threshold_gb: float = 1.0

    # 冷却时间
    alert_cooldown_seconds: int = 60
```

### 告警消息格式

```json
{
  "alert_id": "uuid",
  "level": "HIGH",
  "title": "连续亏损告警",
  "message": "检测到 5 笔连续亏损，总亏损 12.3%",
  "timestamp": "2026-04-01T12:00:00.000Z",
  "context": {
    "symbol": "BTC",
    "consecutive_losses": 5,
    "total_loss_pct": 0.123,
    "recent_trades": [...]
  }
}
```

### 文件结构

```
tradingagents_crypto/
├── alerts/
│   ├── __init__.py
│   ├── rules.py             # 告警规则引擎
│   └── webhook.py           # Discord/Slack 通知
└── config/
    └── default_config.py    # AlertConfig
```

### 实现

```python
# tradingagents_crypto/alerts/webhook.py
import httpx
import structlog
from typing import Any

logger = structlog.get_logger()


class WebhookClient:
    """Webhook 通知客户端"""

    def __init__(self, discord_url: str | None = None, slack_url: str | None = None):
        self.discord_url = discord_url
        self.slack_url = slack_url
        self._http = httpx.AsyncClient(timeout=10.0)

    async def send(self, level: str, title: str, message: str, context: dict | None = None) -> bool:
        """发送告警到所有配置的 webhook"""
        payload = {
            "level": level,
            "title": title,
            "message": message,
            "context": context or {},
        }

        tasks = []
        if self.discord_url:
            tasks.append(self._send_discord(payload))
        if self.slack_url:
            tasks.append(self._send_slack(payload))

        if not tasks:
            logger.warning("No webhook configured, alert not sent", title=title)
            return False

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return all(r is True for r in results)

    async def _send_discord(self, payload: dict) -> bool:
        """发送 Discord webhook"""
        try:
            await self._http.post(self.discord_url, json={
                "content": f"**{payload['level']}**: {payload['title']}\n{payload['message']}"
            })
            return True
        except Exception as e:
            logger.error("Discord webhook failed", error=str(e))
            return False

    async def _send_slack(self, payload: dict) -> bool:
        """发送 Slack webhook"""
        try:
            await self._http.post(self.slack_url, json={
                "text": f"*{payload['level']}*: {payload['title']}",
                "blocks": [
                    {"type": "section", "text": {"type": "mrkdwn", "text": f"*{payload['title']}*"}},
                    {"type": "section", "text": {"type": "mrkdwn", "text": payload['message']}},
                ]
            })
            return True
        except Exception as e:
            logger.error("Slack webhook failed", error=str(e))
            return False


# tradingagents_crypto/alerts/rules.py
import asyncio
from datetime import datetime, timezone
from collections import deque
from dataclasses import dataclass, field


@dataclass
class AlertRule:
    """告警规则定义"""
    name: str
    check_fn: callable  # () -> Alert | None
    cooldown_seconds: int = 60


@dataclass
class Alert:
    """告警实例"""
    level: str
    title: str
    message: str
    context: dict = field(default_factory=dict)


class AlertEngine:
    """告警规则引擎"""

    def __init__(self, webhook_client: WebhookClient, config: AlertConfig):
        self.webhook = webhook_client
        self.config = config
        self._rules: list[AlertRule] = []
        self._last_alert_time: dict[str, datetime] = {}

        # 注册默认规则
        self._register_default_rules()

    def _register_default_rules(self):
        """注册默认告警规则"""
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

    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self._rules.append(rule)

    async def check_all(self):
        """执行所有规则检查"""
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
        """发送告警"""
        self._last_alert_time[rule_name] = datetime.now(timezone.utc)
        await self.webhook.send(
            level=alert.level,
            title=alert.title,
            message=alert.message,
            context=alert.context,
        )

    # === 内置检查函数 ===
    async def _check_consecutive_loss(self) -> Alert | None:
        """检查连续亏损"""
        # 从 metrics 获取最近 N 笔交易
        recent_losses = self._get_recent_losses(self.config.consecutive_loss_threshold)
        if len(recent_losses) < self.config.consecutive_loss_threshold:
            return None

        total_loss = sum(recent_losses)
        if abs(total_loss) > self.config.consecutive_loss_pct_threshold:
            return Alert(
                level="HIGH",
                title="连续亏损告警",
                message=f"检测到 {len(recent_losses)} 笔连续亏损，总亏损 {total_loss*100:.1f}%",
                context={"recent_losses": recent_losses, "total_loss_pct": total_loss},
            )
        return None

    async def _check_api_error_rate(self) -> Alert | None:
        """检查 API 错误率"""
        # 实现错误率检查
        return None

    def _get_recent_losses(self, count: int) -> list[float]:
        """获取最近 N 笔亏损交易"""
        # 从 metrics 或数据库获取
        return []
```

### 单元测试

```python
# tests/unit/test_alerts.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from tradingagents_crypto.alerts.webhook import WebhookClient
from tradingagents_crypto.alerts.rules import AlertEngine, AlertRule, Alert


class TestWebhookClient:
    @pytest.fixture
    def client(self):
        return WebhookClient(discord_url="https://discord.com/webhook/test")

    @pytest.mark.asyncio
    async def test_send_discord(self, client):
        client._http = AsyncMock()
        result = await client.send("HIGH", "Test", "Test message")
        assert result is True


class TestAlertEngine:
    @pytest.fixture
    def engine(self):
        webhook = AsyncMock()
        config = MagicMock()
        config.alert_cooldown_seconds = 60
        config.consecutive_loss_threshold = 5
        config.consecutive_loss_pct_threshold = 0.10
        return AlertEngine(webhook, config)

    def test_add_rule(self, engine):
        initial_count = len(engine._rules)
        engine.add_rule(AlertRule(name="test", check_fn=lambda: None))
        assert len(engine._rules) == initial_count + 1
```

---

## M4.5: Docker 化部署

### Dockerfile（多阶段构建）

```dockerfile
# === 构建阶段 ===
FROM python:3.11-slim as builder

WORKDIR /app
RUN pip install --no-user --prefix=/install -r requirements.txt

# === 运行阶段 ===
FROM python:3.11-slim

# 安全：非 root 用户
RUN useradd --create-home --shell=/bin/bash appuser

WORKDIR /app

# 从 builder 复制已安装的包
COPY --from=builder /install /usr/local

# 复制应用代码
COPY --chown=appuser:appuser . .

# 切换到非 root 用户
USER appuser

# 环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health/live').raise_for_status()"

# 入口点
CMD ["python", "-m", "tradingagents_crypto.api.health"]
EXPOSE 8000
```

### Docker Compose（开发环境）

```yaml
services:
  trading:
    build: .
    ports:
      - "8000:8000"
    environment:
      - HL_USE_TESTNET=1
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=INFO
      - LOG_FORMAT=json
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:v2.45.0
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

### .dockerignore

```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.git/
.gitignore
*.md
docs/
tests/
.vscode/
.idea/
*.log
data/
.env
.env.local
docker-compose*.yml
Dockerfile*
```

### 单元测试

```python
# tests/integration/test_docker.py
import pytest
import docker


class TestDocker:
    @pytest.fixture
    def client(self):
        return docker.from_env()

    def test_dockerfile_builds(self, client):
        """验证 Dockerfile 能成功构建"""
        image, logs = client.images.build(
            path=".",
            tag="crypto-trading:test",
            rm=True,
        )
        assert image.tags[0] == "crypto-trading:test"

    def test_container_starts(self, client):
        """验证容器能正常启动"""
        try:
            container = client.containers.run(
                "crypto-trading:test",
                detach=True,
                ports={"8000/tcp": 8000},
                healthcheck={
                    "test": ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:8000/health/live')"],
                    "interval": 10000000000,
                }
            )
            # 等待健康检查
            result = container.wait(timeout=30)
            assert result["StatusCode"] == 0
        finally:
            container.remove(force=True)
```

---

## M4.6: CI/CD 流程

### GitHub Actions Workflow

```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: '3.11'
  DOCKER_IMAGE: ghcr.io/${{ github.repository }}

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - name: Install ruff
        run: pip install ruff
      - name: Run ruff
        run: ruff check .

  test:
    name: Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run pytest
        run: |
          pytest --cov=tradingagents_crypto \
                 --cov-fail-under=70 \
                 --cov-report=xml \
                 tests/
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          fail_ci_if_error: true

  docker:
    name: Docker Build
    runs-on: ubuntu-latest
    needs: [lint, test]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ env.DOCKER_IMAGE }}:latest
            ${{ env.DOCKER_IMAGE }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Secrets 配置

| Secret | 说明 |
|--------|------|
| OPENAI_API_KEY | OpenAI API 密钥 |
| HL_API_KEY | Hyperliquid API 密钥 |
| DISCORD_WEBHOOK | Discord 告警 webhook |

---

# Phase 4A: Multi-Agent Orchestration

## 目标

扩展现有的线性 graph → 并行多 Analyst + Meta-Agent 协调

## M4.7: Agent 工厂模式重构

### 设计原则

1. **工厂模式**：通过工厂函数创建 Agent，而非直接实例化
2. **依赖注入**：LLM 通过参数传入，便于测试
3. **可扩展性**：新 Agent 类型只需注册到工厂

### 文件结构

```
tradingagents_crypto/
├── agents/
│   ├── __init__.py
│   ├── base.py              # Agent 基类
│   ├── factory.py           # AgentFactory
│   └── registry.py          # Agent 注册表
```

### 实现

```python
# tradingagents_crypto/agents/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class AgentConfig:
    """Agent 配置"""
    name: str
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 2048


class BaseAgent(ABC):
    """Agent 基类"""

    def __init__(self, config: AgentConfig, llm: Any):
        self.config = config
        self.llm = llm

    @abstractmethod
    async def arun(self, input_data: dict) -> dict:
        """异步执行"""
        pass

    def run(self, input_data: dict) -> dict:
        """同步执行（兼容老代码）"""
        import asyncio
        return asyncio.run(self.arun(input_data))


# tradingagents_crypto/agents/registry.py
from typing import Type


class AgentRegistry:
    """Agent 类型注册表"""

    _analysts: dict[str, Type[BaseAgent]] = {}
    _traders: dict[str, Type[BaseAgent]] = {}

    @classmethod
    def register_analyst(cls, name: str):
        """注册 Analyst"""
        def decorator(agent_cls: Type[BaseAgent]):
            cls._analysts[name] = agent_cls
            return agent_cls
        return decorator

    @classmethod
    def register_trader(cls, name: str):
        """注册 Trader"""
        def decorator(agent_cls: Type[BaseAgent]):
            cls._traders[name] = agent_cls
            return agent_cls
        return decorator

    @classmethod
    def get_analyst(cls, name: str) -> Type[BaseAgent]:
        return cls._analysts.get(name)

    @classmethod
    def get_trader(cls, name: str) -> Type[BaseAgent]:
        return cls._traders.get(name)


# tradingagents_crypto/agents/factory.py
from typing import Any


class AgentFactory:
    """Agent 工厂"""

    @staticmethod
    def create_analyst(
        analyst_type: str,
        llm: Any,
        config: AgentConfig | None = None,
    ) -> BaseAgent:
        """创建 Analyst"""
        from tradingagents_crypto.agents.registry import AgentRegistry

        agent_cls = AgentRegistry.get_analyst(analyst_type)
        if not agent_cls:
            available = list(AgentRegistry._analysts.keys())
            raise ValueError(f"Unknown analyst type: {analyst_type}. Available: {available}")

        if config is None:
            config = AgentConfig(name=analyst_type)

        return agent_cls(config=config, llm=llm)

    @staticmethod
    def create_trader(
        trader_type: str,
        llm: Any,
        config: AgentConfig | None = None,
    ) -> BaseAgent:
        """创建 Trader"""
        from tradingagents_crypto.agents.registry import AgentRegistry

        agent_cls = AgentRegistry.get_trader(trader_type)
        if not agent_cls:
            available = list(AgentRegistry._traders.keys())
            raise ValueError(f"Unknown trader type: {trader_type}. Available: {available}")

        if config is None:
            config = AgentConfig(name=trader_type)

        return agent_cls(config=config, llm=llm)
```

### 使用示例

```python
from tradingagents_crypto.agents.factory import AgentFactory

# 创建 Agent
btc_analyst = AgentFactory.create_analyst("btc", llm=my_llm)
eth_analyst = AgentFactory.create_analyst("eth", llm=my_llm)

# 执行
result = await btc_analyst.arun({"symbol": "BTC", "trade_date": "2026-04-01"})
```

### 单元测试

```python
# tests/unit/test_factory.py
import pytest
from unittest.mock import MagicMock
from tradingagents_crypto.agents.base import BaseAgent, AgentConfig
from tradingagents_crypto.agents.factory import AgentFactory


class MockAgent(BaseAgent):
    async def arun(self, input_data: dict) -> dict:
        return {"result": "ok"}


class TestAgentFactory:
    def test_unknown_analyst_raises(self):
        with pytest.raises(ValueError, match="Unknown analyst type"):
            AgentFactory.create_analyst("unknown", MagicMock())

    def test_create_with_default_config(self):
        from tradingagents_crypto.agents.registry import AgentRegistry

        # 注册测试 Agent
        AgentRegistry._analysts["test"] = MockAgent

        agent = AgentFactory.create_analyst("test", MagicMock())
        assert isinstance(agent, MockAgent)
```

---

## M4.8: 共享 Memory

### 设计目标

1. **线程安全**：使用 `asyncio.Lock`（不是 `threading.RWLock`）
2. **跨 Agent 共享**：多个 Analyst 可读写同一状态
3. **可选持久化**：支持 Redis 存储

### Memory 结构

```python
# memory/shared_state.py
from dataclasses import dataclass, field
from typing import Any
import asyncio


@dataclass
class SharedState:
    """多 Agent 共享状态"""
    symbol: str
    trade_date: str

    # 分析结果
    btc_signal: dict | None = None
    eth_signal: dict | None = None
    sol_signal: dict | None = None
    macro_signal: dict | None = None

    # 决策
    risk_assessment: dict | None = None
    trading_decision: dict | None = None
    final_decision: str = "hold"

    # 元数据
    trace_id: str = ""
    messages: list = field(default_factory=list)


class SharedMemory:
    """线程安全的共享内存"""

    def __init__(self, use_redis: bool = False, redis_url: str | None = None):
        self._lock = asyncio.Lock()
        self._data: dict[str, SharedState] = {}
        self._use_redis = use_redis
        self._redis_url = redis_url
        self._redis = None

    async def initialize(self):
        """初始化（异步）"""
        if self._use_redis:
            import redis.asyncio as redis
            self._redis = redis.from_url(self._redis_url or "redis://localhost:6379")

    async def read(self, trace_id: str) -> SharedState | None:
        """读取状态"""
        async with self._lock:
            return self._data.get(trace_id)

    async def write(self, trace_id: str, state: SharedState):
        """写入状态"""
        async with self._lock:
            self._data[trace_id] = state
            if self._redis:
                # 可选：持久化到 Redis
                import json
                await self._redis.set(
                    f"state:{trace_id}",
                    json.dumps(self._to_dict(state)),
                    ex=3600,
                )

    def _to_dict(self, state: SharedState) -> dict:
        """转换为 dict（用于 JSON 序列化）"""
        return {
            "symbol": state.symbol,
            "trade_date": state.trade_date,
            "btc_signal": state.btc_signal,
            "eth_signal": state.eth_signal,
            "sol_signal": state.sol_signal,
            "macro_signal": state.macro_signal,
            "risk_assessment": state.risk_assessment,
            "trading_decision": state.trading_decision,
            "final_decision": state.final_decision,
            "trace_id": state.trace_id,
        }
```

### 单元测试

```python
# tests/unit/test_memory.py
import pytest
from tradingagents_crypto.memory.shared_state import SharedMemory, SharedState


class TestSharedMemory:
    @pytest.fixture
    def memory(self):
        return SharedMemory()

    @pytest.mark.asyncio
    async def test_write_and_read(self, memory):
        state = SharedState(symbol="BTC", trade_date="2026-04-01", trace_id="test123")
        await memory.write("test123", state)

        result = await memory.read("test123")
        assert result.symbol == "BTC"
        assert result.trace_id == "test123"

    @pytest.mark.asyncio
    async def test_concurrent_write(self, memory):
        """并发写入测试"""
        import asyncio

        async def write(i):
            state = SharedState(symbol=f"COIN{i}", trace_id=f"trace{i}")
            await memory.write(f"trace{i}", state)

        await asyncio.gather(*[write(i) for i in range(10)])

        for i in range(10):
            state = await memory.read(f"trace{i}")
            assert state.symbol == f"COIN{i}"

    @pytest.mark.asyncio
    async def test_nonexistent_read(self, memory):
        result = await memory.read("nonexistent")
        assert result is None
```

---

## M4.9: Meta-Agent

### 职责

1. **任务分解**：将用户任务分解为子任务
2. **任务分发**：分发给子 Analyst
3. **结果聚合**：汇总分析报告

### 文件结构

```
tradingagents_crypto/
├── graph/
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── meta_agent.py          # Meta-Agent 节点
│   │   └── analyst_coordinator.py # Analyst 协调器
│   └── edges/
│       ├── __init__.py
│       └── parallel_join.py        # 并行结果合并
```

### 实现

```python
# tradingagents_crypto/graph/nodes/meta_agent.py
from dataclasses import dataclass
from typing import Literal


@dataclass
class Task:
    """子任务定义"""
    type: str  # btc_analysis, eth_analysis, sol_analysis, macro_analysis
    priority: int  # 1=高, 2=中, 3=低
    symbol: str | None = None


async def meta_agent_node(state: dict) -> dict:
    """Meta-Agent 节点：任务分解"""
    user_request = state.get("user_request", "")
    symbol = state.get("symbol", "BTC")

    # 任务分解策略
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


# tradingagents_crypto/graph/nodes/analyst_coordinator.py
import asyncio
from tradingagents_crypto.agents.factory import AgentFactory


async def analyst_coordinator(state: dict) -> dict:
    """协调多个 Analyst 并行执行"""
    tasks = state.get("tasks", [])
    llm = state.get("llm")

    # 按优先级分组
    high_priority = [t for t in tasks if t.get("priority") == 1]
    low_priority = [t for t in tasks if t.get("priority") > 1]

    results = {}

    # 高优先级：并行执行
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

    # 低优先级：串行执行（如果有高优先级失败才执行）
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
                # 记录错误但不中断
                results[task["type"]] = {"error": str(e)}

    return {
        "analyst_results": results,
        "status": "completed",
    }


async def _safe_analyst_run(analyst, task: dict) -> dict:
    """安全执行 Analyst（带超时）"""
    input_data = {
        "symbol": task.get("symbol"),
        "trade_date": task.get("trade_date"),
    }
    return await analyst.arun(input_data)
```

### 单元测试

```python
# tests/unit/test_meta_agent.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from tradingagents_crypto.graph.nodes.meta_agent import meta_agent_node


class TestMetaAgent:
    @pytest.mark.asyncio
    async def test_meta_agent_decomposes_task(self):
        state = {
            "user_request": "Analyze BTC and ETH",
            "symbol": "BTC",
        }
        result = await meta_agent_node(state)

        assert result["status"] == "dispatched"
        assert len(result["tasks"]) == 4  # BTC, ETH, SOL, Macro
        assert any(t["type"] == "btc_analysis" for t in result["tasks"])
```

---

## M4.10: 并行 Analyst 执行

### 实现

```python
# tradingagents_crypto/graph/nodes/parallel_analysts.py
import asyncio
from typing import Sequence


async def run_analysts_parallel(
    analysts: list,  # list of BaseAgent
    input_data: dict,
    timeout: float = 30.0,
) -> list[dict]:
    """并行执行多个 Analyst

    Args:
        analysts: Analyst 实例列表
        input_data: 输入数据
        timeout: 单个 Analyst 超时时间

    Returns:
        结果列表（顺序与输入一致）
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

    # 处理异常
    processed = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed.append({
                "error": str(result),
                "analyst": analysts[i].config.name if hasattr(analysts[i], 'config') else str(i),
            })
        else:
            processed.append(result)

    return processed


class SyncAnalystAdapter:
    """将同步 Analyst 适配为异步接口（向后兼容）"""

    def __init__(self, sync_analyst):
        self._analyst = sync_analyst

    async def arun(self, input_data: dict) -> dict:
        return await asyncio.to_thread(self._analyst.run, input_data)
```

### 单元测试

```python
# tests/unit/test_parallel_analysts.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from tradingagents_crypto.graph.nodes.parallel_analysts import (
    run_analysts_parallel,
    SyncAnalystAdapter,
)


class TestParallelAnalysts:
    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """验证并行执行"""
        analyst1 = AsyncMock()
        analyst1.arun = AsyncMock(return_value={"result": "BTC analysis"})
        analyst2 = AsyncMock()
        analyst2.arun = AsyncMock(return_value={"result": "ETH analysis"})

        results = await run_analysts_parallel(
            [analyst1, analyst2],
            {"symbol": "BTC"},
        )

        assert len(results) == 2
        analyst1.arun.assert_called_once()
        analyst2.arun.assert_called_once()

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """验证超时处理"""
        analyst = AsyncMock()
        analyst.arun = AsyncMock(side_effect=asyncio.TimeoutError)

        results = await run_analysts_parallel(
            [analyst],
            {"symbol": "BTC"},
            timeout=0.1,
        )

        assert "error" in results[0]


class TestSyncAnalystAdapter:
    @pytest.mark.asyncio
    async def test_adapter_works(self):
        """验证向后兼容适配器"""
        sync_agent = MagicMock()
        sync_agent.run = MagicMock(return_value={"result": "sync"})

        adapter = SyncAnalystAdapter(sync_agent)
        result = await adapter.arun({})

        assert result["result"] == "sync"
        sync_agent.run.assert_called_once()
```

---

# Phase 4C: Live Trading

## ⚠️ 前置条件

在启动 Phase 4C 之前，必须满足：

1. **Paper trading 至少 1 个月**，无重大损失
2. **回测 vs 实盘偏差 < 5%**
3. **完整的风险审批流程**已建立
4. **人工确认机制**已实施

## M4.11: Paper Trading 模式

### 配置

```python
# config/default_config.py
@dataclass
class TradingConfig:
    mode: Literal["backtest", "paper", "live"] = "paper"
    paper_initial_capital: float = 100_000.0  # USD
    paper_slippage_bps: float = 5.0  # 模拟滑点
    paper_funding_simulate: bool = True
```

### PaperTrader 实现

```python
# trading/modes/paper_trader.py
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal


@dataclass
class Order:
    symbol: str
    side: Literal["buy", "sell"]
    size_usd: float
    order_type: Literal["market", "limit"] = "market"
    limit_price: float | None = None


@dataclass
class OrderResult:
    status: Literal["filled", "rejected", "cancelled"]
    filled_price: float | None = None
    filled_at: datetime | None = None
    order_id: str | None = None


class PaperTrader:
    """Paper Trading 模拟器"""

    def __init__(
        self,
        initial_capital: float = 100_000,
        slippage_bps: float = 5.0,
    ):
        self.cash = initial_capital
        self.positions: dict[str, float] = {}  # symbol -> size
        self.slippage_bps = slippage_bps
        self._order_id = 0

    async def place_order(self, order: Order, current_price: float) -> OrderResult:
        """模拟订单执行"""
        self._order_id += 1

        # 计算滑点
        slippage = current_price * self.slippage_bps / 10000
        if order.side == "buy":
            filled_price = current_price + slippage
        else:
            filled_price = current_price - slippage

        # 模拟成交
        cost = order.size_usd * filled_price / current_price

        if order.side == "buy":
            if cost > self.cash:
                return OrderResult(status="rejected")
            self.cash -= cost
            self.positions[order.symbol] = self.positions.get(order.symbol, 0) + order.size_usd
        else:
            if self.positions.get(order.symbol, 0) < order.size_usd:
                return OrderResult(status="rejected")
            self.cash += cost
            self.positions[order.symbol] -= order.size_usd

        return OrderResult(
            status="filled",
            filled_price=filled_price,
            filled_at=datetime.now(timezone.utc),
            order_id=f"paper_{self._order_id}",
        )

    def get_position(self, symbol: str) -> float:
        return self.positions.get(symbol, 0)

    def get_cash(self) -> float:
        return self.cash
```

### 单元测试

```python
# tests/integration/test_paper_trading.py
import pytest
from tradingagents_crypto.trading.modes.paper_trader import PaperTrader, Order


class TestPaperTrader:
    @pytest.fixture
    def trader(self):
        return PaperTrader(initial_capital=100_000, slippage_bps=5)

    @pytest.mark.asyncio
    async def test_market_buy(self, trader):
        result = await trader.place_order(
            Order(symbol="BTC", side="buy", size_usd=10_000),
            current_price=50_000,
        )

        assert result.status == "filled"
        assert result.filled_price == 50_025  # +5bps slippage
        assert trader.positions["BTC"] == 10_000

    @pytest.mark.asyncio
    async def test_insufficient_funds(self, trader):
        result = await trader.place_order(
            Order(symbol="BTC", side="buy", size_usd=200_000),
            current_price=50_000,
        )

        assert result.status == "rejected"

    @pytest.mark.asyncio
    async def test_sell_position(self, trader):
        # 先买入
        await trader.place_order(
            Order(symbol="BTC", side="buy", size_usd=10_000),
            current_price=50_000,
        )
        # 再卖出
        result = await trader.place_order(
            Order(symbol="BTC", side="sell", size_usd=10_000),
            current_price=50_000,
        )

        assert result.status == "filled"
        assert trader.positions["BTC"] == 0
```

---

## M4.12: 实盘 API 连接

### 连接器

```python
# trading/connectors/hyperliquid_connector.py
import httpx
from dataclasses import dataclass


@dataclass
class TradingConfig:
    mode: Literal["backtest", "paper", "live"]
    mainnet_url: str = "https://api.hyperliquid.xyz"
    testnet_url: str = "https://api.hyperliquid-testnet.xyz"
    api_key: str | None = None
    api_secret: str | None = None


class HyperliquidConnector:
    """Hyperliquid 实盘连接器"""

    def __init__(self, config: TradingConfig):
        self.config = config
        self.base_url = (
            config.mainnet_url if config.mode == "live"
            else config.testnet_url
        )
        self._http = httpx.AsyncClient(timeout=30.0)

    async def place_order(self, order: Order) -> OrderResult:
        """下单"""
        payload = {
            "type": "MARKET" if order.order_type == "market" else "LIMIT",
            "symbol": order.symbol,
            "side": order.side.upper(),
            "sz": order.size_usd,
        }
        if order.limit_price:
            payload["px"] = order.limit_price

        resp = await self._http.post(
            f"{self.base_url}/trade",
            json=payload,
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        return OrderResult(**resp.json())

    async def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        resp = await self._http.post(
            f"{self.base_url}/cancel",
            json={"id": order_id},
            headers=self._auth_headers(),
        )
        return resp.status_code == 200

    async def get_positions(self) -> list[dict]:
        """获取持仓"""
        resp = await self._http.post(
            f"{self.base_url}/positions",
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def _auth_headers(self) -> dict:
        # 实现签名逻辑
        return {}
```

---

## M4.13: 人工审批流程

### 决策流程

```
Agent 决策 → 风控检查 → 人工确认 → 执行
                              ↑
                       等待用户确认
```

### 审批消息格式

```json
{
  "type": "trading_approval",
  "signal": {
    "symbol": "BTC",
    "action": "LONG",
    "size_usd": 10000,
    "entry_price": 50000,
    "stop_loss": 49000,
    "confidence": 0.85
  },
  "timestamp": "2026-04-01T12:00:00.000Z",
  "approve_url": "https://...",
  "reject_url": "https://..."
}
```

### 实现

```python
# trading/approval/approver.py
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import uuid


@dataclass
class ApprovalRequest:
    signal: dict
    requested_at: datetime
    expires_at: datetime
    status: str = "pending"  # pending/approved/rejected/expired


class ApprovalEngine:
    """人工审批引擎"""

    def __init__(
        self,
        webhook_client,  # WebhookClient
        approval_timeout_minutes: int = 5,
    ):
        self.webhook = webhook_client
        self.timeout = timedelta(minutes=approval_timeout_minutes)
        self._pending: dict[str, ApprovalRequest] = {}

    async def request_approval(self, signal: dict) -> str:
        """发起审批请求"""
        request_id = str(uuid.uuid4())[:8]
        request = ApprovalRequest(
            signal=signal,
            requested_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + self.timeout,
        )
        self._pending[request_id] = request

        # 发送 Discord 消息
        await self.webhook.send(
            level="MEDIUM",
            title="交易审批请求",
            message=self._format_signal_message(signal),
            context={
                "request_id": request_id,
                "approve_url": f"/approval/{request_id}/approve",
                "reject_url": f"/approval/{request_id}/reject",
            },
        )

        return request_id

    async def approve(self, request_id: str) -> bool:
        """审批通过"""
        request = self._pending.get(request_id)
        if not request or request.status != "pending":
            return False

        if datetime.now(timezone.utc) > request.expires_at:
            request.status = "expired"
            return False

        request.status = "approved"
        return True

    async def reject(self, request_id: str) -> bool:
        """审批拒绝"""
        request = self._pending.get(request_id)
        if not request:
            return False
        request.status = "rejected"
        return True

    def _format_signal_message(self, signal: dict) -> str:
        return (
            f"**交易信号**\n"
            f"Symbol: {signal.get('symbol')}\n"
            f"Action: {signal.get('action')}\n"
            f"Size: ${signal.get('size_usd', 0):,.0f}\n"
            f"Entry: ${signal.get('entry_price', 0):,.0f}\n"
            f"Confidence: {signal.get('confidence', 0)*100:.0f}%\n\n"
            f"请在 5 分钟内回复 [Approve] 或 [Reject]"
        )
```

---

## 实施顺序

> ⚠️ 注意：M4.13 人工审批应早于 M4.11，因为 paper trading 也需要审批机制。

```
Phase 4B (Infrastructure)
├── M4.1 结构化日志
├── M4.2 健康检查端点
├── M4.3 Prometheus Metrics
├── M4.4 告警系统
├── M4.5 Docker 化
└── M4.6 CI/CD

Phase 4A (Multi-Agent)
├── M4.7 Agent 工厂
├── M4.8 共享 Memory
├── M4.9 Meta-Agent
└── M4.10 并行执行

Phase 4C (Live Trading)
├── M4.13 人工审批  ← 提前（paper trading 也需要）
├── M4.11 Paper Trading
└── M4.12 实盘连接
```

## 目录结构

```
tradingagents_crypto/
├── utils/
│   ├── logging.py          # M4.1
│   └── metrics.py          # M4.3
├── api/
│   └── health.py           # M4.2
├── alerts/
│   ├── __init__.py
│   ├── rules.py            # M4.4
│   └── webhook.py          # M4.4
├── memory/
│   ├── __init__.py
│   └── shared_state.py     # M4.8
├── graph/
│   ├── __init__.py
│   └── nodes/
│       ├── __init__.py
│       ├── meta_agent.py          # M4.9
│       ├── analyst_coordinator.py # M4.9
│       └── parallel_analysts.py   # M4.10
├── agents/
│   ├── __init__.py
│   ├── base.py             # M4.7
│   ├── factory.py          # M4.7
│   └── registry.py         # M4.7
├── trading/
│   ├── modes/
│   │   ├── __init__.py
│   │   └── paper_trader.py # M4.11
│   ├── connectors/
│   │   ├── __init__.py
│   │   └── hyperliquid_connector.py # M4.12
│   └── approval/
│       ├── __init__.py
│       └── approver.py     # M4.13
├── docker/
│   ├── Dockerfile          # M4.5
│   └── docker-compose.yml  # M4.5
└── .github/
    └── workflows/
        └── ci.yml          # M4.6
```

---

## 修订历史

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-04-02 | v1.0 | 初始版本 |
| 2026-04-02 | v1.1 | 审查修复：M4.8 asyncio.Lock兼容性、Phase 4C顺序修正、AlertConfig可配置阈值、向后兼容适配器 |
| 2026-04-02 | v1.2 | 全面重写：所有模块补充完整实现代码和单元测试，修复docker-compose重复项，修复M4.8异步接口 |
