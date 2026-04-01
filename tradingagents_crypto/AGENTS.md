# AGENTS.md — Crypto TradingAgents

**项目**: TradingAgents Crypto Edition
**定位**: Hyperliquid / ETH / Solana 永续合约多 Agent 分析系统
**模式**: 纯分析信号（不执行交易）
**状态**: Phase 1 进行中
**当前里程碑**: M1.1 环境搭建（待启动）

---

## 项目背景

原 [TradingAgents](https://github.com/TauricResearch/TradingAgents) 是股票/传统金融市场多 Agent 交易分析框架。本项目是其 Crypto 专用 Fork，专注加密货币永续合约市场。

### 核心差异对照

| 维度 | 原项目（股票） | 本项目（Crypto） |
|------|-------------|----------------|
| 市场时间 | 交易日（周一~五） | **24/7 无休** |
| 数据源 | Yahoo Finance | Hyperliquid API + 链上数据 |
| 基本面 | 财报/年报 | **链上指标（TVL/活跃地址/Gas）** |
| 风控 | 股票仓位 | **合约保证金/清算风险** |
| 特有数据 | 内部人交易 | **资金费率/OI/订单簿深度** |

---

## 已确认的设计决策

### 架构
- **继承 + 扩展**：不破坏原项目，新建 `tradingagents_crypto/` 包
- **单一大脑，多链分析师**：各链有专属 Analyst，汇聚到统一 Trader
- **Phase 顺序**：Phase 1（Hyperliquid 单链）→ Phase 2（ETH/SOL 多链）→ Phase 3（风控+回测）

### 技术
- **Python 3.10**（Hyperliquid SDK 限制）
- **付费 API 可用**（Dune / Alchemy / CoinGecko Pro 等）
- **独立虚拟环境**：`tradingagents-crypto`

### 分析
- **交易对**：通用（任意币种）
- **主时间周期**：`1h`（推荐），`4h` 和 `1d` 作为辅助参考
- **数据源优先级**：Hyperliquid Info API（Phase 1）、CoinGecko（价格参考）、Alchemy/Dune（链上数据 Phase 2+）

---

## 目录结构

```
tradingagents_crypto/
├── AGENTS.md                    # 本文件
├── README.md                    # 项目说明
│
├── tradingagents_crypto/       # 主包
│   ├── __init__.py
│   │
│   ├── default_config.py        # Crypto 专用配置
│   │
│   ├── dataflows/               # 数据层
│   │   ├── __init__.py
│   │   ├── hyperliquid/         # Phase 1：Hyperliquid 数据
│   │   │   ├── __init__.py
│   │   │   ├── api.py           # SDK 封装
│   │   │   ├── candles.py       # K 线数据
│   │   │   ├── funding.py       # 资金费率
│   │   │   ├── orderbook.py     # 订单簿
│   │   │   ├── oi.py            # 持仓量
│   │   │   └── trades.py        # 成交历史
│   │   │
│   │   ├── ethereum/            # Phase 2：ETH 数据
│   │   │   └── ...
│   │   │
│   │   └── solana/              # Phase 2：SOL 数据
│   │       └── ...
│   │
│   ├── agents/                  # Agent 层
│   │   ├── __init__.py
│   │   │
│   │   ├── base.py              # 基础 Agent 类
│   │   │
│   │   ├── analysts/            # 分析师
│   │   │   ├── hyperliquid_perp_analyst.py   # Phase 1
│   │   │   ├── ethereum_onchain_analyst.py   # Phase 2
│   │   │   ├── solana_dex_analyst.py         # Phase 2
│   │   │   └── cross_chain_macro_analyst.py   # Phase 2
│   │   │
│   │   ├── researchers/         # 多空研究员（复用原项目）
│   │   │   └── ...
│   │   │
│   │   ├── risk_mgmt/            # 风控（扩展原项目）
│   │   │   ├── liquidation_scenator.py
│   │   │   └── vol_analyst.py
│   │   │
│   │   └── trader/              # 交易员（扩展支持多链）
│   │       └── crypto_trader.py
│   │
│   └── graph/                   # LangGraph 图
│       ├── crypto_trading_graph.py   # Phase 1
│       └── backtest_engine.py        # Phase 3
│
├── tests/                       # 测试
│   └── ...
│
└── scripts/                    # 辅助脚本
    └── ...
```

---

## 数据流总体设计

```
输入: $SYMBOL, $DATE, $CHAIN(s)
    ↓
┌─────────────────────────────────────────────────┐
│  Chain-Specific Analysts（并行）                  │
│  ├─ HL Perp Analyst                              │
│  │   → 资金费率 / OI / 订单簿 / 成交量 / 波动率   │
│  ├─ ETH OnChain Analyst（Phase 2）               │
│  │   → Gas / 活跃地址 / TVL / DEX 流动性         │
│  └─ SOL DEX Analyst（Phase 2）                    │
│      → DEX 池状态 / SPL 代币流                   │
└─────────────────────────────────────────────────┘
    ↓ 汇聚
┌─────────────────────────────────────────────────┐
│  Cross-Chain Macro Analyst（Phase 2）             │
│  → BTC.D / 稳定币流动 / 跨链相关性               │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│  Bull/Bear Researchers（辩论）                   │
│  → 多空双方基于数据辩论                          │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│  Trader Agent                                    │
│  → 多链汇总报告 / 方向判断 / 仓位建议             │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│  Risk Management                                │
│  → 清算风险 / 波动率阈值 / 杠杆验证              │
└─────────────────────────────────────────────────┘
    ↓
Portfolio Manager → 输出交易信号（不执行）
```

---

## 开发规范

### 数据层规范

**统一数据格式**（所有链数据必须对齐）：

```python
@dataclass
class OHLCV:
    symbol: str           # "BTC" / "ETH"
    chain: str            # "hyperliquid" / "ethereum" / "solana"
    timestamp: int        # Unix 秒
    open: float
    high: float
    low: float
    close: float
    volume: float
    # 可选扩展
    funding_rate: float | None = None
    open_interest: float | None = None
    mark_price: float | None = None
```

**缓存策略**：
- K 线数据本地 SQLite 缓存
- 缓存文件命名：`{symbol}_{chain}_{interval}_{start}_{end}.db`
- 回测时按 `timestamp <= curr_date` 过滤，防止未来数据泄露

**数据新鲜度**：
- 实盘分析：K 线数据不超过 5 分钟陈旧
- 回测模式：使用缓存数据 + 时间戳验证

---

### Agent 设计规范

**每个 Analyst 必须输出**：
1. `summary`: 简短结论（1-2 句）
2. `signals`: 关键信号列表（dict）
3. `metrics`: 具体数值（dict）
4. `narrative`: 详细分析文本

**Prompt 模板**：
```
你是一个 [链] [角色] 分析师。
给定以下数据：[数据描述]
请分析并输出 JSON 格式：
{
    "summary": "短期偏多/偏空/中性，核心理由",
    "signals": {
        "信号名": "信号值及方向"
    },
    "metrics": {
        "指标名": 数值
    },
    "narrative": "详细分析（供 Researcher 辩论用）"
}
```

---

### 配置规范

**mode 切换**（在 `default_config.py`）：

```python
# 模式 A：股票（原生）
config["mode"] = "stock"

# 模式 B：Crypto
config["mode"] = "crypto"
config["crypto"] = {
    "primary_chain": "hyperliquid",  # Phase 1
    # "primary_chain": "ethereum",    # Phase 2
    # "primary_chain": "solana",       # Phase 2
    "default_interval": "1h",
    "supported_chains": ["hyperliquid"],
}
```

---

### 代码风格

- **类型提示**：必须使用，所有函数参数和返回值标注类型
- **Docstring**：每个公开函数/类必须有 `"""` 说明
- **异常处理**：数据获取失败应返回空值/默认值，不应让整个流程崩溃
- **日志**：关键节点使用 `logging`，禁止 `print`

---

## 测试规范

- 数据层函数必须单测（mock HTTP 响应）
- Agent 输出格式必须校验（schema validation）
- 回测引擎必须有一组确定性测试用例

---

## 已知的风险点（持续更新）

| 风险 | 影响 | 状态 |
|------|------|------|
| Hyperliquid SDK Python 3.10 限制 | 与原项目环境冲突 | ✅ 用独立虚拟环境隔离 |
| CoinGecko 免费版限速 | 回测数据不完整 | ✅ Phase 1 先用 HL 官方数据 |
| 三链数据同步复杂 | 架构复杂度上升 | ✅ Phase 1 先单链 |
| 链上数据需要付费节点 | 数据成本 | ⚠️ 待 Phase 2 评估 Dune/Alchemy |

---

## 任务分解

Phase 1 已分解为 8 个里程碑，共 50 个子任务。详见 `tasks/` 目录。

| 里程碑 | 状态 | 任务数 | 累计工时 |
|--------|------|--------|---------|
| M1.0 SDK 验证 | ✅ 完成 | 1 | 4h |
| M1.1 环境搭建 | 🔵 待启动 | 4 | 3h |
| M1.2 数据层 | 🔵 待启动 | 9 | 13h |
| M1.3 配置层 | 🔵 待启动 | 5 | 4h |
| M1.4 技术指标 | 🔵 待启动 | 5 | 8h |
| M1.5 Agent 层 | 🔵 待启动 | 6 | 15h |
| M1.6 Graph 集成 | 🔵 待启动 | 7 | 13h |
| M1.7 端到端测试 | 🔵 待启动 | 9 | 9h |

**Phase 1 总工时**: ~69 小时（约 10 个工作日）

---

## 参考资料

- [Hyperliquid Python SDK](https://github.com/hyperliquid-dex/hyperliquid-python-sdk)
- [Hyperliquid API Docs](https://hyperliquid.gitbook.io/hyperliquid)
- [原 TradingAgents 项目](https://github.com/TauricResearch/TradingAgents)
- [Dune Analytics API](https://docs.dune.com)
- [Alchemy Ethereum API](https://docs.alchemy.com)

---

*本文件记录项目架构决策和开发规范。代码细节参见各模块 Docstring。*
