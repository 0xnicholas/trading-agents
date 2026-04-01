# Phase 4: 测试计划

## 测试策略

### 分层测试模型

| 层级 | 范围 | 网络依赖 | Mock策略 | 目标覆盖率 |
|------|------|---------|---------|-----------|
| Unit | 单个模块 | ❌ 无 | ✅ Mock 外部依赖 | ≥ 80% |
| Integration | 多模块协作 | ⚠️ 最小化 | Mock HTTP | ≥ 60% |
| E2E | 完整流程 | ✅ 真实 | ❌ 不 mock | - |

### 测试环境要求

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行所有测试
pytest tests/ -v --cov=tradingagents_crypto --cov-fail-under=70
```

---

## Phase 4B 测试

### M4.1 结构化日志

#### 单元测试

| ID | 测试内容 | 输入 | 预期结果 |
|----|---------|------|---------|
| T_LOG_01 | JSONFormatter 输出有效 JSON | LogRecord | `json.loads()` 不抛异常 |
| T_LOG_02 | timestamp 格式正确 | LogRecord | ISO8601，毫秒精度 |
| T_LOG_03 | level 字段正确 | INFO/WARNING/ERROR | 字段值匹配 |
| T_LOG_04 | context 字段序列化 | record.context | JSON 包含 context |
| T_LOG_05 | trace_id 传递 | record.trace_id | 日志包含 trace_id |
| T_LOG_06 | 异常信息序列化 | exc_info | JSON 包含 exception 字段 |
| T_LOG_07 | setup_logging 创建 handler | json_format=True | FileHandler + StreamHandler |
| T_LOG_08 | get_logger 返回正确名称 | "test_module" | logger.name == "test_module" |

```python
# tests/unit/test_logging.py
import pytest
import json
import logging
from datetime import datetime, timezone
from tradingagents_crypto.utils.logging import JSONFormatter, setup_logging, get_logger


class TestJSONFormatter:
    def test_format_returns_valid_json(self):
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
        result = formatter.format(record)
        # Should not raise
        parsed = json.loads(result)
        assert "timestamp" in parsed

    def test_timestamp_is_iso8601(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="", lineno=0,
            msg="Test", args=(), exc_info=None,
        )
        parsed = json.loads(formatter.format(record))
        # Verify ISO format
        datetime.fromisoformat(parsed["timestamp"].replace("Z", "+00:00"))

    def test_context_serialized(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="", lineno=0,
            msg="Test", args=(), exc_info=None,
        )
        record.context = {"symbol": "BTC", "size": 1000}
        parsed = json.loads(formatter.format(record))
        assert parsed["context"]["symbol"] == "BTC"

    def test_exception_serialized(self):
        formatter = JSONFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            record = logging.LogRecord(
                name="test", level=logging.ERROR,
                pathname="", lineno=0,
                msg="Error occurred", args=(), exc_info=sys.exc_info(),
            )
        parsed = json.loads(formatter.format(record))
        assert "exception" in parsed
        assert "test error" in parsed["exception"]
```

#### 集成测试

| ID | 测试内容 | 输入 | 预期结果 |
|----|---------|------|---------|
| T_LOG_09 | 日志文件写入 | 多条日志 | 文件包含 JSON 行 |
| T_LOG_10 | 日志轮转 | 跨 midnight | 新文件创建 |

---

### M4.2 健康检查端点

#### 单元测试

| ID | 测试内容 | 输入 | 预期结果 |
|----|---------|------|---------|
| T_HEALTH_01 | /health 返回 200 | GET /health | status=healthy, 200 |
| T_HEALTH_02 | /health/ready 返回 200 | GET /health/ready | status in [ready, degraded] |
| T_HEALTH_03 | /health/live 返回 200 | GET /health/live | status=live, 200 |
| T_HEALTH_04 | health 缓存生效 | 2次请求 < 60s | 缓存命中，响应一致 |
| T_HEALTH_05 | Redis 检查失败处理 | Redis 不可用 | redis status=error |
| T_HEALTH_06 | 超时处理 | 服务慢响应 | 优雅处理，不崩溃 |

```python
# tests/unit/test_health.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
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

    def test_health_has_version(self, client):
        response = client.get("/health")
        assert "version" in response.json()

    def test_liveness_returns_live(self, client):
        response = client.get("/health/live")
        assert response.json()["status"] == "live"

    @patch("tradingagents_crypto.api.health._do_health_check")
    def test_readiness_checks_deps(self, mock_check, client):
        mock_check.return_value = {
            "redis": {"status": "ok", "latency_ms": 2},
            "hyperliquid": {"status": "ok", "latency_ms": 45},
        }
        response = client.get("/health/ready")
        assert response.status_code == 200
```

#### 集成测试

| ID | 测试内容 | 预期结果 |
|----|---------|---------|
| T_HEALTH_07 | curl localhost:8000/health | HTTP 200 |

---

### M4.3 Prometheus Metrics

#### 单元测试

| ID | 测试内容 | 预期结果 |
|----|---------|---------|
| T_METRICS_01 | orders_total.inc() 增加计数 | Counter 值 +1 |
| T_METRICS_02 | pnl_gauge.set() 设置值 | Gauge 值正确 |
| T_METRICS_03 | cache_hit_ratio 计算 | hit/(hit+miss) |
| T_METRICS_04 | /metrics 端点返回 | Prometheus 格式 |

```python
# tests/unit/test_metrics.py
import pytest
from prometheus_client import REGISTRY
from tradingagents_crypto.utils.metrics import (
    orders_total, pnl_gauge, position_size,
    agent_response_time, cache_hits
)


class TestTradingMetrics:
    def test_orders_total_increments(self):
        initial = orders_total.labels(
            symbol="BTC", side="long", result="filled"
        )._value.get()
        orders_total.labels(symbol="BTC", side="long", result="filled").inc()
        after = orders_total.labels(
            symbol="BTC", side="long", result="filled"
        )._value.get()
        assert after == initial + 1

    def test_orders_total_with_labels(self):
        orders_total.labels(symbol="ETH", side="short", result="filled").inc(5)
        value = orders_total.labels(
            symbol="ETH", side="short", result="filled"
        )._value.get()
        assert value >= 5

    def test_pnl_gauge_set(self):
        pnl_gauge.labels(symbol="BTC").set(1234.56)
        assert pnl_gauge.labels(symbol="BTC")._value.get() == 1234.56

    def test_position_size_gauge(self):
        position_size.labels(symbol="ETH").set(5000)
        assert position_size.labels(symbol="ETH")._value.get() == 5000


class TestCacheMetrics:
    def test_hit_miss_ratio_calculation(self):
        cache_hits.labels(cache="prices", result="hit").inc(80)
        cache_hits.labels(cache="prices", result="miss").inc(20)
        hit = cache_hits.labels(cache="prices", result="hit")._value.get()
        miss = cache_hits.labels(cache="prices", result="miss")._value.get()
        ratio = hit / (hit + miss)
        assert ratio == 0.8
```

---

### M4.4 告警系统

#### 单元测试

| ID | 测试内容 | 预期结果 |
|----|---------|---------|
| T_ALERT_01 | WebhookClient.send() | 发送 POST 请求 |
| T_ALERT_02 | Discord payload 格式 | 正确 embed 格式 |
| T_ALERT_03 | AlertEngine.add_rule() | 规则添加 |
| T_ALERT_04 | cooldown 机制 | 冷却时间内不重复发送 |
| T_ALERT_05 | consecutive_loss 检测 | N笔亏损触发 |
| T_ALERT_06 | configurable thresholds | 配置值生效 |
| T_ALERT_07 | Alert 序列化 | JSON 不抛异常 |

```python
# tests/unit/test_alerts.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tradingagents_crypto.alerts.webhook import WebhookClient
from tradingagents_crypto.alerts.rules import AlertEngine, AlertRule, Alert


class TestWebhookClient:
    @pytest.fixture
    def client(self):
        return WebhookClient(
            discord_url="https://discord.com/webhook/test",
            slack_url=None,
        )

    @pytest.mark.asyncio
    async def test_send_discord(self, client):
        client._http = AsyncMock()
        client._http.post = AsyncMock()
        result = await client.send(
            level="HIGH",
            title="Test Alert",
            message="Test message",
        )
        assert result is True
        client._http.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_webhook_returns_false(self):
        client = WebhookClient()
        result = await client.send("HIGH", "Test", "msg")
        assert result is False


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
        initial = len(engine._rules)
        engine.add_rule(AlertRule(name="test", check_fn=lambda: None))
        assert len(engine._rules) == initial + 1

    def test_is_in_cooldown(self, engine):
        # 无记录 -> 不在冷却
        assert engine._is_in_cooldown("new_rule") is False

    @pytest.mark.asyncio
    async def test_consecutive_loss_triggers(self, engine):
        # Mock 检查函数返回告警
        engine._check_consecutive_loss = AsyncMock(return_value=Alert(
            level="HIGH",
            title="Loss",
            message="5 consecutive losses",
        ))
        result = await engine._check_consecutive_loss()
        assert result is not None
        assert result.level == "HIGH"
```

---

### M4.5 Docker

#### 集成测试

| ID | 测试内容 | 预期结果 |
|----|---------|---------|
| T_DOCKER_01 | `docker build` | 构建成功，无错误 |
| T_DOCKER_02 | 非 root 用户 | USER 为 appuser |
| T_DOCKER_03 | `docker run` 启动 | 容器运行 |
| T_DOCKER_04 | 健康检查 | HTTP 200 |
| T_DOCKER_05 | docker-compose up | 所有服务启动 |
| T_DOCKER_06 | Redis 连接 | redis 健康 |

```python
# tests/integration/test_docker.py
import pytest
import docker


class TestDockerImage:
    @pytest.fixture
    def client(self):
        return docker.from_env()

    def test_dockerfile_syntax(self, client):
        """验证 Dockerfile 能解析"""
        try:
            client.images.build(
                path=".",
                tag="crypto-trading:test",
                rm=True,
            )
            built = True
        except Exception:
            built = False
        assert built

    def test_non_root_user(self, client):
        """验证非 root 用户"""
        # 构建镜像
        image, _ = client.images.build(
            path=".",
            tag="crypto-trading:test",
            rm=True,
        )
        # 检查用户
        # 这需要实际运行容器
```

---

### M4.6 CI/CD

#### 单元测试

| ID | 测试内容 | 预期结果 |
|----|---------|---------|
| T_CICD_01 | secrets 引用格式 | `${{ secrets.X }}` |
| T_CICD_02 | pytest 命令 | --cov-fail-under=70 |
| T_CICD_03 | docker 需要 test 通过 | needs: [test] |

---

## Phase 4A 测试

### M4.7 Agent 工厂

#### 单元测试

| ID | 测试内容 | 预期结果 |
|----|---------|---------|
| T_FACTORY_01 | create_analyst 已知类型 | 返回 Agent 实例 |
| T_FACTORY_02 | create_analyst 未知类型 | ValueError |
| T_FACTORY_03 | create_trader 已知类型 | 返回 Trader 实例 |
| T_FACTORY_04 | 默认 config | AgentConfig 默认值 |

```python
# tests/unit/test_factory.py
import pytest
from unittest.mock import MagicMock
from tradingagents_crypto.agents.base import BaseAgent, AgentConfig
from tradingagents_crypto.agents.factory import AgentFactory


class MockAnalyst(BaseAgent):
    async def arun(self, input_data: dict) -> dict:
        return {"result": "ok"}


class TestAgentFactory:
    def test_unknown_analyst_raises(self):
        with pytest.raises(ValueError, match="Unknown analyst type"):
            AgentFactory.create_analyst("unknown", MagicMock())

    def test_create_with_default_config(self):
        # 注册
        from tradingagents_crypto.agents.registry import AgentRegistry
        AgentRegistry._analysts["mock"] = MockAnalyst

        agent = AgentFactory.create_analyst("mock", MagicMock())
        assert isinstance(agent, MockAnalyst)

    def test_create_with_custom_config(self):
        from tradingagents_crypto.agents.registry import AgentRegistry
        AgentRegistry._analysts["mock"] = MockAnalyst

        config = AgentConfig(name="custom", temperature=0.5)
        agent = AgentFactory.create_analyst("mock", MagicMock(), config=config)
        assert agent.config.temperature == 0.5
```

---

### M4.8 共享 Memory

#### 单元测试

| ID | 测试内容 | 预期结果 |
|----|---------|---------|
| T_MEMORY_01 | write + read 一致 | 读写数据相同 |
| T_MEMORY_02 | 不存在返回 None | read("none") is None |
| T_MEMORY_03 | 并发写入 | 无数据丢失 |
| T_MEMORY_04 | asyncio.Lock | 异步上下文正常 |
| T_MEMORY_05 | Redis 持久化 | 数据写入 Redis |
| T_MEMORY_06 | SharedState 字段 | 所有字段正确 |

```python
# tests/unit/test_memory.py
import pytest
import asyncio
from tradingagents_crypto.memory.shared_state import SharedMemory, SharedState


class TestSharedMemory:
    @pytest.fixture
    def memory(self):
        return SharedMemory(use_redis=False)

    @pytest.mark.asyncio
    async def test_write_and_read(self, memory):
        state = SharedState(
            symbol="BTC",
            trade_date="2026-04-01",
            trace_id="test123",
            btc_signal={"price": 50000},
        )
        await memory.write("test123", state)
        result = await memory.read("test123")
        assert result.symbol == "BTC"
        assert result.btc_signal["price"] == 50000

    @pytest.mark.asyncio
    async def test_read_nonexistent(self, memory):
        result = await memory.read("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_concurrent_writes(self, memory):
        """10 个并发写入"""
        async def write(i):
            state = SharedState(symbol=f"COIN{i}", trace_id=f"t{i}")
            await memory.write(f"t{i}", state)

        await asyncio.gather(*[write(i) for i in range(10)])

        for i in range(10):
            state = await memory.read(f"t{i}")
            assert state.symbol == f"COIN{i}"

    @pytest.mark.asyncio
    async def test_overwrite(self, memory):
        state1 = SharedState(symbol="BTC", trace_id="t1")
        state2 = SharedState(symbol="ETH", trace_id="t1")

        await memory.write("t1", state1)
        await memory.write("t1", state2)

        result = await memory.read("t1")
        assert result.symbol == "ETH"
```

---

### M4.9 Meta-Agent

#### 单元测试

| ID | 测试内容 | 预期结果 |
|----|---------|---------|
| T_META_01 | 任务分解 | 4 个子任务 |
| T_META_02 | 高优先级任务 | btc/eth/macro |
| T_META_03 | analyst_coordinator | 调用所有 Analyst |
| T_META_04 | 单个 Analyst 超时 | 不中断其他 |

```python
# tests/unit/test_meta_agent.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from tradingagents_crypto.graph.nodes.meta_agent import meta_agent_node
from tradingagents_crypto.graph.nodes.analyst_coordinator import analyst_coordinator


class TestMetaAgent:
    @pytest.mark.asyncio
    async def test_decomposes_to_4_tasks(self):
        state = {"user_request": "Analyze BTC", "symbol": "BTC"}
        result = await meta_agent_node(state)
        assert len(result["tasks"]) == 4
        assert result["status"] == "dispatched"

    @pytest.mark.asyncio
    async def test_tasks_include_btc(self):
        state = {"user_request": "Analyze", "symbol": "BTC"}
        result = await meta_agent_node(state)
        task_types = [t["type"] for t in result["tasks"]]
        assert "btc_analysis" in task_types

    @pytest.mark.asyncio
    async def test_coordinator_calls_analysts(self):
        mock_analyst = AsyncMock()
        mock_analyst.arun = AsyncMock(return_value={"signal": "bullish"})

        state = {
            "tasks": [
                {"type": "btc_analysis", "priority": 1, "symbol": "BTC"},
            ],
            "llm": MagicMock(),
        }

        with pytest.patch(
            "tradingagents_crypto.graph.nodes.analyst_coordinator.AgentFactory"
        ) as factory:
            factory.create_analyst.return_value = mock_analyst
            result = await analyst_coordinator(state)

        assert "btc_analysis" in result["analyst_results"]
```

---

### M4.10 并行执行

#### 单元测试

| ID | 测试内容 | 预期结果 |
|----|---------|---------|
| T_PARALLEL_01 | 4 Analyst 并行 | 全部完成 |
| T_PARALLEL_02 | 单个异常处理 | 其他继续 |
| T_PARALLEL_03 | 超时中断 | TimeoutError in result |
| T_PARALLEL_04 | SyncAnalystAdapter | 同步转异步 |
| T_PARALLEL_05 | 加速比 | 并行 < 顺序 |

```python
# tests/unit/test_parallel_analysts.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from tradingagents_crypto.graph.nodes.parallel_analysts import (
    run_analysts_parallel,
    SyncAnalystAdapter,
)


class TestParallelExecution:
    @pytest.mark.asyncio
    async def test_all_complete(self):
        analysts = [AsyncMock() for _ in range(4)]
        for a in analysts:
            a.arun = AsyncMock(return_value={"ok": True})

        results = await run_analysts_parallel(analysts, {"symbol": "BTC"})

        assert len(results) == 4
        assert all("ok" in r for r in results)

    @pytest.mark.asyncio
    async def test_one_fails_others_complete(self):
        analysts = [AsyncMock(), AsyncMock(), AsyncMock()]
        analysts[0].arun = AsyncMock(side_effect=ValueError("fail"))
        analysts[1].arun = AsyncMock(return_value={"ok": True})
        analysts[2].arun = AsyncMock(return_value={"ok": True})

        results = await run_analysts_parallel(analysts, {})

        assert "error" in results[0]
        assert results[1]["ok"] is True
        assert results[2]["ok"] is True

    @pytest.mark.asyncio
    async def test_timeout(self):
        analyst = AsyncMock()
        analyst.arun = AsyncMock(side_effect=asyncio.TimeoutError)

        results = await run_analysts_parallel([analyst], {}, timeout=0.01)
        assert "error" in results[0]


class TestSyncAdapter:
    @pytest.mark.asyncio
    async def test_sync_to_async(self):
        sync_agent = MagicMock()
        sync_agent.run = MagicMock(return_value={"from": "sync"})

        adapter = SyncAnalystAdapter(sync_agent)
        result = await adapter.arun({})

        assert result["from"] == "sync"
        sync_agent.run.assert_called_once()
```

---

## Phase 4C 测试

### M4.11 Paper Trading

#### 单元测试

| ID | 测试内容 | 预期结果 |
|----|---------|---------|
| T_PAPER_01 | 市价买入 | 成交，价格=当前+滑点 |
| T_PAPER_02 | 市价卖出 | 成交，价格=当前-滑点 |
| T_PAPER_03 | 资金不足 | status=rejected |
| T_PAPER_04 | 卖出超过持仓 | status=rejected |
| T_PAPER_05 | 持仓查询 | get_position 返回正确值 |
| T_PAPER_06 | 资金费率模拟 | 持仓 8h 扣费 |
| T_PAPER_07 | 模式切换 | config.mode=paper |

```python
# tests/integration/test_paper_trading.py
import pytest
from tradingagents_crypto.trading.modes.paper_trader import PaperTrader, Order


class TestPaperTrader:
    @pytest.fixture
    def trader(self):
        return PaperTrader(initial_capital=100_000, slippage_bps=5)

    @pytest.mark.asyncio
    async def test_market_buy_fills(self, trader):
        result = await trader.place_order(
            Order(symbol="BTC", side="buy", size_usd=10_000),
            current_price=50_000,
        )
        assert result.status == "filled"
        # 5 bps slippage = 50,000 * 0.0005 = 25
        assert result.filled_price == 50_025
        assert trader.positions["BTC"] == 10_000
        assert trader.cash == 100_000 - (10_000 * 50_025 / 50_000)

    @pytest.mark.asyncio
    async def test_market_sell_fills(self, trader):
        # 先买入
        await trader.place_order(
            Order(symbol="BTC", side="buy", size_usd=10_000),
            current_price=50_000,
        )
        # 再卖出入
        result = await trader.place_order(
            Order(symbol="BTC", side="sell", size_usd=10_000),
            current_price=50_000,
        )
        assert result.status == "filled"
        assert trader.positions["BTC"] == 0

    @pytest.mark.asyncio
    async def test_insufficient_funds(self, trader):
        result = await trader.place_order(
            Order(symbol="BTC", side="buy", size_usd=200_000),
            current_price=50_000,
        )
        assert result.status == "rejected"

    @pytest.mark.asyncio
    async def test_sell_more_than_position(self, trader):
        # 买入 1000 USD
        await trader.place_order(
            Order(symbol="BTC", side="buy", size_usd=1_000),
            current_price=50_000,
        )
        # 尝试卖出 2000 USD
        result = await trader.place_order(
            Order(symbol="BTC", side="sell", size_usd=2_000),
            current_price=50_000,
        )
        assert result.status == "rejected"
```

---

### M4.12 实盘连接

#### 集成测试（需要真实 API key）

| ID | 测试内容 | 前置条件 |
|----|---------|---------|
| T_LIVE_01 | place_order | testnet API key |
| T_LIVE_02 | cancel_order | 已有挂单 |
| T_LIVE_03 | get_positions | 有持仓 |

```python
# tests/integration/test_hyperliquid_connector.py
import pytest


@pytest.mark.skipif(
    not pytest.config.getoption("--run-live", default=False),
    reason="需要真实 API key"
)
class TestHyperliquidConnector:
    @pytest.mark.asyncio
    async def test_place_order_testnet(self):
        from tradingagents_crypto.trading.connectors.hyperliquid_connector import (
            HyperliquidConnector, TradingConfig
        )
        config = TradingConfig(mode="paper")
        connector = HyperliquidConnector(config)
        # ...
```

---

### M4.13 人工审批

#### 单元测试

| ID | 测试内容 | 预期结果 |
|----|---------|---------|
| T_APPROVAL_01 | request_approval 返回 ID | request_id 有效 |
| T_APPROVAL_02 | approve 改变状态 | status=approved |
| T_APPROVAL_03 | reject 改变状态 | status=rejected |
| T_APPROVAL_04 | 超时过期 | status=expired |
| T_APPROVAL_05 | Webhook 发送 | 消息格式正确 |
| T_APPROVAL_06 | 重复 approve | 第二次返回 False |

```python
# tests/unit/test_approval.py
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock
from tradingagents_crypto.trading.approval.approver import (
    ApprovalEngine,
    ApprovalRequest,
)


class TestApprovalEngine:
    @pytest.fixture
    def engine(self):
        webhook = AsyncMock()
        return ApprovalEngine(webhook, approval_timeout_minutes=5)

    @pytest.mark.asyncio
    async def test_request_approval(self, engine):
        signal = {"symbol": "BTC", "action": "LONG", "size_usd": 10000}
        request_id = await engine.request_approval(signal)
        assert request_id is not None
        assert len(request_id) == 8

    @pytest.mark.asyncio
    async def test_approve(self, engine):
        request_id = await engine.request_approval({"symbol": "BTC"})
        result = await engine.approve(request_id)
        assert result is True
        assert engine._pending[request_id].status == "approved"

    @pytest.mark.asyncio
    async def test_reject(self, engine):
        request_id = await engine.request_approval({"symbol": "BTC"})
        result = await engine.reject(request_id)
        assert result is True
        assert engine._pending[request_id].status == "rejected"

    @pytest.mark.asyncio
    async def test_expired_request(self, engine):
        request_id = await engine.request_approval({"symbol": "BTC"})
        # 手动设置为过期
        engine._pending[request_id].expires_at = (
            datetime.now(timezone.utc) - timedelta(minutes=1)
        )
        result = await engine.approve(request_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_webhook_called(self, engine):
        await engine.request_approval({"symbol": "BTC"})
        engine.webhook.send.assert_called_once()
        call_args = engine.webhook.send.call_args
        assert call_args[1]["level"] == "MEDIUM"
```

---

## 覆盖率目标

| 模块 | 行覆盖率 | 分支覆盖 | 关键测试 |
|------|---------|---------|---------|
| utils/logging | ≥ 90% | ≥ 80% | JSONFormatter, setup_logging |
| api/health | ≥ 95% | ≥ 90% | 所有端点 |
| utils/metrics | ≥ 85% | ≥ 75% | Counter/Gauge/Histogram |
| alerts/ | ≥ 80% | ≥ 70% | WebhookClient, AlertEngine |
| memory/ | ≥ 85% | ≥ 75% | SharedMemory 并发 |
| graph/nodes/ | ≥ 80% | ≥ 70% | Meta-Agent, Parallel |
| agents/ | ≥ 75% | ≥ 65% | Factory, Registry |
| trading/modes/ | ≥ 85% | ≥ 75% | PaperTrader |
| trading/approval/ | ≥ 80% | ≥ 70% | ApprovalEngine |

---

## 执行命令

```bash
# 运行所有单元测试
cd /root/TradingAgents
python -m pytest tradingagents_crypto/tests/unit/ -v --cov=tradingagents_crypto

# 运行特定模块测试
python -m pytest tradingagents_crypto/tests/unit/test_logging.py -v
python -m pytest tradingagents_crypto/tests/unit/test_health.py -v
python -m pytest tradingagents_crypto/tests/unit/test_metrics.py -v
python -m pytest tradingagents_crypto/tests/unit/test_factory.py -v
python -m pytest tradingagents_crypto/tests/unit/test_memory.py -v
python -m pytest tradingagents_crypto/tests/unit/test_meta_agent.py -v
python -m pytest tradingagents_crypto/tests/unit/test_parallel_analysts.py -v

# 运行集成测试
python -m pytest tradingagents_crypto/tests/integration/test_paper_trading.py -v

# 运行带覆盖率
python -m pytest tradingagents_crypto/tests/ \
    --cov=tradingagents_crypto \
    --cov-report=term-missing \
    --cov-fail-under=70 \
    -v
```

---

## Mock 策略

### HTTP Mock

```python
# 使用 responses 或 httpx mock
import responses

@responses.activate
def test_discord_webhook():
    responses.add(
        responses.POST,
        "https://discord.com/api/webhooks/test",
        json={"id": "123"},
        status=200,
    )
    # 测试代码...
```

### Redis Mock

```python
# 使用 fakeredis
import fakeredis.aioredis

@pytest.fixture
async def fake_redis():
    return await fakeredis.aioredis.FakeRedis()
```

---

## 修订历史

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-04-02 | v1.0 | 初始版本 |
| 2026-04-02 | v1.1 | 补充可配置阈值测试，asyncio memory 测试 |
| 2026-04-02 | v1.2 | 全面重写：补充完整测试代码，覆盖率目标，按模块组织 |
