# AGENTS.md — Crypto TradingAgents

**项目**: tradingagents_crypto
**版本**: Phase 1-4 完成
**定位**: Hyperliquid / Ethereum / Solana 永续合约多 Agent 分析交易系统
**最后更新**: 2026-04-02

---

## 系统架构

```
输入: $SYMBOL, $DATE, $CHAIN(s)
    ↓
┌─────────────────────────────────────────────────────┐
│  Chain-Specific Analysts（并行）                       │
│  ├─ Hyperliquid Perp Analyst                          │
│  │   → 资金费率 / OI / 订单簿 / K线 / 成交量         │
│  ├─ ETH OnChain Analyst（扩展）                       │
│  │   → Gas / 活跃地址 / TVL / DEX 流动性            │
│  └─ SOL DEX/Meme Analyst（扩展）                      │
│      → DEX 池状态 / SPL 代币流 / Meme 情绪          │
└─────────────────────────────────────────────────────┘
    ↓ 汇聚
┌─────────────────────────────────────────────────────┐
│  Cross-Chain Macro Analyst（扩展）                     │
│  → BTC.D / 稳定币流动 / 跨链相关性                  │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│  Bull/Bear Researchers（辩论）                        │
│  → 多空双方基于数据辩论                              │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│  Trader Agent                                        │
│  → 多链汇总报告 / 方向判断 / 仓位建议                │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│  Risk Management                                    │
│  → 清算风险 / 波动率阈值 / 杠杆验证                 │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│  Portfolio Manager / Approval Workflow               │
│  → 审批决策 / 信号输出                             │
└─────────────────────────────────────────────────────┘
    ↓
PaperTrading / HyperliquidConnector（实盘）
```

---

## Agent 类型

### 1. Analysts（分析师）

| Agent | 文件 | 职责 |
|-------|------|------|
| HyperliquidPerpAnalyst | `agents/analysts/hyperliquid_perp_analyst.py` | Hyperliquid 永续合约分析 |
| EthereumOnChainAnalyst | `agents/analysts/` | ETH 链上数据分析 |
| SolanaDEXAnalyst | `agents/analysts/` | Solana DEX 分析 |
| CrossChainMacroAnalyst | `agents/analysts/` | 跨链宏观分析 |

### 2. Researchers（研究员）

| Agent | 文件 | 职责 |
|-------|------|------|
| BullResearcher | `agents/researchers/` | 多方论点 |
| BearResearcher | `agents/researchers/` | 空方论点 |

### 3. Traders（交易员）

| Agent | 文件 | 职责 |
|-------|------|------|
| CryptoTrader | `agents/traders/crypto_trader.py` | 交易决策 |
| MetaAgent | `graph/nodes/meta_agent.py` | 任务分解 |

### 4. Risk Management（风险管理）

| Agent | 文件 | 职责 |
|-------|------|------|
| HVAnalyst | `agents/risk_mgmt/hv_analyst.py` | 历史波动率分析 |
| LiquidationSpectator | `agents/risk_mgmt/` | 清算风险评估 |
| RiskManager | `agents/risk_mgmt/` | 综合风险管理 |

### 5. Management（管理）

| Agent | 文件 | 职责 |
|-------|------|------|
| PortfolioManager | `agents/managers/portfolio_manager.py` | 组合管理 |
| AnalystCoordinator | `graph/nodes/analyst_coordinator.py` | 分析师协调 |

---

## 目录结构

```
tradingagents_crypto/
├── agents/
│   ├── __init__.py
│   ├── base.py                 # Agent 基类
│   ├── factory.py              # AgentFactory
│   ├── registry.py             # AgentRegistry
│   ├── schema.py               # Pydantic schemas
│   ├── analysts/
│   │   └── hyperliquid_perp_analyst.py
│   ├── researchers/
│   ├── risk_mgmt/
│   │   ├── hv_analyst.py
│   │   └── ...
│   ├── traders/
│   │   └── crypto_trader.py
│   └── managers/
│       └── portfolio_manager.py
│
├── graph/
│   ├── crypto_trading_graph.py  # LangGraph 主图
│   └── nodes/
│       ├── meta_agent.py
│       ├── analyst_coordinator.py
│       └── ...
│
├── dataflows/
│   └── hyperliquid/
│       ├── api.py             # HLClient SDK 封装
│       ├── candles.py         # K 线数据
│       ├── funding.py         # 资金费率
│       ├── orderbook.py       # 订单簿
│       ├── oi.py             # 持仓量
│       └── cache.py           # SQLite TTL 缓存
│
├── backtest/
│   ├── backtest_engine.py     # 回测引擎
│   ├── data_cache.py          # 回测数据缓存
│   ├── reporting.py           # 报告生成
│   ├── benchmark.py           # 基准对比
│   ├── slippage_estimator.py  # 滑点估算
│   └── funding_simulator.py   # 资金费率模拟
│
├── trading/
│   ├── paper_engine.py        # 模拟交易引擎
│   ├── hyperliquid.py         # HyperliquidConnector
│   └── approval.py            # 审批工作流
│
├── alerts/
│   ├── webhook.py             # Webhook 客户端
│   └── rules.py               # 告警规则引擎
│
├── utils/
│   ├── logging.py             # JSON 结构化日志
│   └── metrics.py            # Prometheus Metrics
│
├── api/
│   └── health.py              # FastAPI 健康检查
│
└── config/
    └── default_config.py       # 默认配置
```

---

## 数据流

### 并行分析师执行

```python
async def run_analysts_parallel(
    analysts: list[BaseAgent],
    data: dict,
    timeout: int = 120
) -> dict[str, Any]:
    """并行运行多个分析师，带超时控制"""
```

### 工作流状态

```
TRADING_INIT
    ↓
ANALYST_COORDINATION
    ↓ (并行)
ANALYST_EXECUTION → [HL_Analyst, ETH_Analyst, SOL_Analyst, ...]
    ↓ (汇聚)
RESEARCHER_DEBATE → [Bull_Researcher, Bear_Researcher]
    ↓
TRADER_DECISION
    ↓
RISK_ASSESSMENT
    ↓
PORTFOLIO_MANAGER
    ↓
APPROVAL_WORKFLOW (可选)
    ↓
TRADE_EXECUTION → PaperTrading / HyperliquidConnector
```

---

## 配置

### AgentConfig

```python
@dataclass
class AgentConfig:
    model_name: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 120
    retry_count: int = 3
```

### 交易模式

```python
# Paper Trading（默认）
config["trading_mode"] = "paper"

# Live Trading（需审批）
config["trading_mode"] = "live"
config["approval_required"] = True
```

---

## 测试

| 测试文件 | 说明 |
|---------|------|
| `tests/unit/test_agents.py` | Agent 配置测试 |
| `tests/unit/test_config.py` | 配置测试 |
| `tests/unit/test_indicators.py` | 技术指标测试 |
| `tests/unit/test_hl_client.py` | Hyperliquid 客户端测试 |
| `tests/unit/test_cache.py` | 缓存测试 |
| `tests/unit/test_utils.py` | 工具函数测试 |
| `tests/unit/test_schema.py` | Schema 验证测试 |
| `tests/unit/test_graph.py` | Graph 测试 |
| `tests/integration/test_btc_e2e.py` | BTC 端到端测试 |
| `tests/integration/test_case1_ma_strategy.py` | MA 策略回测 |
| `tests/integration/test_case2_funding_strategy.py` | 资金费率策略回测 |
| `tests/integration/test_case3_cross_chain.py` | 跨链策略回测 |

---

## 已完成里程碑

| 阶段 | 里程碑 | 状态 |
|------|--------|------|
| Phase 1 | M1.0-M1.6 | ✅ |
| Phase 2 | M2.0 跳过 | ⏭️ |
| Phase 3 | M3.1-M3.5 | ✅ |
| Phase 4 | M4.1-M4.13 | ✅ |

---

*本文件描述系统架构和 Agent 设计。详细实现参见各模块源码。*
