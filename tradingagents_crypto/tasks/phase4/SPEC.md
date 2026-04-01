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
  "timestamp": "2026-04-01T12:00:00Z",
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

### 日志级别规范
| 级别 | 使用场景 |
|------|---------|
| DEBUG | 开发调试，诊断问题 |
| INFO | 正常业务流程（交易开仓/平仓/决策） |
| WARNING | 异常但可恢复（数据缺失、降级） |
| ERROR | 操作失败（API 超时、数据错误） |
| CRITICAL | 系统级故障（连接断开） |

### 输出目标
- Console（开发环境）
- JSON File（生产环境，按天切割）
- 可选：Loki/Datadog

### 实现
```python
# tradingagents_crypto/utils/logging.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": "crypto-trading",
            "module": record.module,
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", ""),
            "context": getattr(record, "context", {}),
        })
```

---

## M4.2: 健康检查端点

### HTTP 端点
```
GET /health          → {"status": "healthy", "timestamp": "..."}
GET /health/ready   → {"status": "ready", "checks": {...}}
GET /health/live    → {"status": "live"}
```

### 健康检查内容
| 检查项 | 超时 | 失败后果 |
|--------|------|---------|
| Redis/Cache 连接 | 2s | healthy但degraded |
| Hyperliquid API | 3s | healthy但degraded |
| LLM API | 5s | healthy但degraded |
| 磁盘空间 | - | healthy |

### 实现
```python
# tradingagents_crypto/api/health.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }
```

---

## M4.3: Prometheus Metrics

### 核心指标
```
# 交易指标
trading_orders_total{symbol, side, result}
trading_pnl_total{symbol}
trading_position_size{symbol}
trading_win_rate{symbol}

# 性能指标
agent_response_time_seconds{agent, operation}
api_request_duration_seconds{endpoint, status}
cache_hit_ratio{cache}

# 系统指标
system_memory_bytes
system_cpu_percent
```

### 实现
```python
from prometheus_client import Counter, Histogram, Gauge

orders_total = Counter(
    "trading_orders_total",
    "Total number of orders",
    ["symbol", "side", "result"]
)
```

---

## M4.4: 告警系统

### 告警规则
| 告警 | 条件 | 严重度 | 通知 |
|------|------|--------|------|
| 连续亏损 | 5笔亏损 > 10% | HIGH | Discord |
| API 错误率 | > 10% in 5min | MEDIUM | Discord |
| 响应超时 | > 30s | MEDIUM | Discord |
| 缓存命中率低 | < 50% in 1h | LOW | 日志 |
| 磁盘空间不足 | < 1GB | HIGH | Discord |

### Webhook 配置
```python
# config/default_config.py
@dataclass
class AlertConfig:
    discord_webhook: str | None = None
    slack_webhook: str | None = None
    alert_level: str = "HIGH"  # LOW/MEDIUM/HIGH
```

---

## M4.5: Docker 化部署

### Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-m", "tradingagents_crypto"]
```

### Docker Compose（开发环境）
```yaml
services:
  trading:
    build: .
    environment:
      - HL_USE_TESTNET=1
    volumes:
      - ./data:/app/data

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
```

---

## M4.6: CI/CD 流程

### GitHub Actions
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Run tests
        run: pytest --cov=tradingagents_crypto
      - name: Lint
        run: ruff check .

  docker:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker
        run: docker build -t crypto-trading:${{ github.sha }} .
```

---

# Phase 4A: Multi-Agent Orchestration

## 目标

扩展现有的线性 graph → 并行多 Analyst + Meta-Agent 协调

## M4.7: Agent 工厂模式重构

### 当前问题
- Analyst 和 Trader 硬编码在 `crypto_trading_graph.py`
- 无法动态配置 Agent 角色
- 无工厂模式，难以扩展

### 重构设计
```python
# agents/factory.py
class AgentFactory:
    @staticmethod
    def create_analyst(
        analyst_type: Literal["btc", "eth", "sol", "macro"],
        llm,
    ) -> Agent:
        ...

    @staticmethod
    def create_trader(
        trader_type: Literal["crypto", "multi_asset"],
        llm,
    ) -> Agent:
        ...

    @staticmethod
    def create_risk_manager(
        llm,
    ) -> Agent:
        ...
```

---

## M4.8: 共享 Memory

### Memory 结构
```python
# memory/shared_state.py
@dataclass
class SharedState:
    """多 Agent 共享状态"""
    symbol: str
    trade_date: str

    # 分析结果
    btc_signal: AnalystReport | None = None
    eth_signal: AnalystReport | None = None
    sol_signal: AnalystReport | None = None
    macro_signal: AnalystReport | None = None

    # 决策
    risk_assessment: RiskAssessment | None = None
    trading_decision: TradingDecision | None = None
    final_decision: str = "hold"

    # 元数据
    trace_id: str = ""
    messages: list[BaseMessage] = field(default_factory=list)
```

### Memory 锁
```python
# 并行读取，串行写入
from threading import RWLock

class SharedMemory:
    def __init__(self):
        self._lock = RWLock()

    def read(self, key) -> Any:
        with self._lock.read:
            return self._data.get(key)

    def write(self, key, value):
        with self._lock.write:
            self._data[key] = value
```

---

## M4.9: Meta-Agent

### Meta-Agent 职责
1. 接收用户任务
2. 分解为子任务
3. 分发给子 Analyst
4. 收集结果
5. 聚合决策

### Graph 结构
```
                    ┌─ BTC Analyst ─┐
                    ├─ ETH Analyst ─┤
START → Meta-Agent ├─ SOL Analyst ─┤→ Risk → Decision → END
                    ├─ Macro Analyst─┤
                    └─ Risk Manager ─┘
```

### 实现
```python
# graph/nodes/meta_agent.py
def meta_agent_node(state: SharedState) -> dict:
    """任务分解 + 分发"""
    sub_tasks = [
        {"type": "btc_analysis", "priority": 1},
        {"type": "eth_analysis", "priority": 1},
        {"type": "sol_analysis", "priority": 2},
        {"type": "macro_analysis", "priority": 1},
    ]
    return {"sub_tasks": sub_tasks, "status": "dispatched"}


# graph/nodes/analyst_coordinator.py
def analyst_coordinator(state: SharedState) -> dict:
    """协调多个 Analyst 并行执行"""
    # 使用 asyncio.gather 并行调用
    results = await gather([
        btc_analyst.run(state.symbol),
        eth_analyst.run(state.symbol),
        sol_analyst.run(state.symbol),
        macro_analyst.run(state.symbol),
    ])
    return {"analyst_results": results}
```

---

## M4.10: 并行 Analyst 执行

### 当前：顺序执行
```python
# 顺序（低效）
btc_signal = btc_analyst.run(symbol)
eth_signal = eth_analyst.run(symbol)
sol_signal = sol_analyst.run(symbol)
```

### 优化后：并行执行
```python
# 并行（高效）
import asyncio

async def run_analysts_parallel(symbol: str):
    tasks = [
        btc_analyst.arun(symbol),
        eth_analyst.arun(symbol),
        sol_analyst.arun(symbol),
        macro_analyst.arun(symbol),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
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

### 模式切换
```python
@dataclass
class TradingConfig:
    mode: Literal["backtest", "paper", "live"] = "paper"
    paper_mode: bool = True  # 模拟订单，不真实成交
```

### Paper Trading 模拟器
```python
# trading/modes/paper_trader.py
class PaperTrader:
    """模拟 Hyperliquid API"""
    def __init__(self, initial_capital: float = 100_000):
        self.cash = initial_capital
        self.positions = {}

    def place_order(self, order: Order) -> OrderResult:
        # 模拟订单执行，返回假成交
        return OrderResult(
            status="filled",
            filled_price=self模拟价格(order),
            filled_at=datetime.now(),
        )
```

---

## M4.12: 实盘 API 连接

### 连接器
```python
# trading/connectors/hyperliquid_connector.py
class HyperliquidConnector:
    def __init__(self, config: TradingConfig):
        self.client = HLClient(base_url=config.mainnet_url)

    def place_order(self, order: Order) -> OrderResult:
        # 真实 API 调用
        return self.client.place_order(order)

    def cancel_order(self, order_id: str) -> bool:
        return self.client.cancel_order(order_id)
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
```
🤖 Trading Signal Detected

Symbol: BTC-PERP
Action: LONG
Size: $10,000
Entry: $50,000
Stop: $49,000
Confidence: 85%

[Approve] [Reject] [Modify Size]
```

---

## 目录结构

```
tradingagents_crypto/
├── utils/
│   ├── logging.py          # M4.1
│   └── metrics.py          # M4.3
├── api/
│   └── health.py          # M4.2
├── alerts/
│   ├── webhook.py         # M4.4
│   └── rules.py           # M4.4
├── docker/
│   ├── Dockerfile         # M4.5
│   └── docker-compose.yml # M4.5
├── .github/workflows/
│   └── ci.yml             # M4.6
├── agents/
│   └── factory.py         # M4.7
├── memory/
│   └── shared_state.py    # M4.8
├── graph/
│   ├── nodes/
│   │   ├── meta_agent.py          # M4.9
│   │   └── analyst_coordinator.py  # M4.10
│   └── edges/
│       └── parallel_join.py        # M4.10
├── trading/
│   ├── modes/
│   │   └── paper_trader.py   # M4.11
│   ├── connectors/
│   │   └── hyperliquid_connector.py  # M4.12
│   └── approval/
│       └── approver.py       # M4.13
└── tests/
    ├── unit/test_logging.py
    ├── unit/test_metrics.py
    ├── integration/test_paper_trading.py
    └── integration/test_meta_agent.py
```

---

## 修订历史

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-04-02 | v1.0 | 初始版本 |
