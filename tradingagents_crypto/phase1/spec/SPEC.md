# Phase 1 完整规格说明书

**版本**: v1.1（修订）
**日期**: 2026-04-01
**状态**: 已批准
**修订说明**: v1.1 修正了 3 项描述错误（meta_and_asset_ctxs 返回格式、get_hl_data 过滤语义、目录结构重复）；新增atr_pct 定义、atr_history 来源说明。
**周期**: 2-3 周
**目标**: Hyperliquid 单链打样，跑通完整 Crypto 版 TradingAgents pipeline

---

## 1. 概述

### 1.1 目的

本规格说明书定义 Phase 1 所有交付物的功能、接口、行为和数据格式，作为开发、测试和验收的基准文件。

### 1.2 范围

Phase 1 交付一个基于 Hyperliquid 永续合约市场的多 Agent 分析系统，仅支持 Hyperliquid 单链数据源，输出结构化分析报告和交易决策。

### 1.3 限制

- **不执行交易**：仅输出分析信号
- **不支持 ETH/SOL 链数据**：Phase 2 扩展
- **不支持回测**：Phase 3 实现
- **不支持 Solana 永续**：Solana 数据仅限现货 DEX
- **Python 3.10**：Hyperliquid SDK 硬性要求

---

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                  CryptoTradingAgentsGraph                │
│  propagate(symbol: str, date: str) → (report, decision) │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Analyst    │ │  Researcher  │ │    Trader    │
│ (Hyperliquid │ │ Bull / Bear  │ │  (汇总决策)  │
│   Perp)      │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
                                          │
                              ┌───────────┴───────────┐
                              ▼                       ▼
                      ┌──────────────┐       ┌──────────────┐
                      │ RiskManager  │       │ PortfolioMgr │
                      │   (简化)     │       │              │
                      └──────────────┘       └──────────────┘
```

### 2.2 数据流

```
输入: symbol (str), date (str)
    ↓
[1] HyperliquidDataBridge.get(symbol, date)
    ├→ get_candles("BTC", "1h", 7)
    ├→ get_candles("BTC", "4h", 7)
    ├→ get_candles("BTC", "1d", 30)
    ├→ get_current_funding("BTC")
    ├→ get_open_interest("BTC")
    └→ get_orderbook("BTC")
    ↓
[2] compute_all_indicators(candles_1h)
    ├→ ATR(14)
    ├→ RSI(14)
    ├→ MACD(12/26/9)
    ├→ Bollinger Bands(20, 2)
    ├→ MA(7, 24, 50, 200)
    └→ OI change rate / Orderbook imbalance / Volatility position
    ↓
[3] HyperliquidPerpAnalyst.analyze(symbol, date, data)
    → LLM call → JSON report
    ↓
[4] BullResearcher / BearResearcher.research(report)
    → LLM call → Bull case / Bear case
    ↓
[5] CryptoTraderAgent.decide(symbol, report, bull, bear)
    → action / size_pct / leverage
    ↓
[6] CryptoRiskManager.evaluate(decision)
    → warnings / adjustments
    ↓
[7] CryptoPortfolioManager.approve(decision, risk_report)
    → final_decision (or reject)
    ↓
输出: (analyst_report: dict, final_decision: dict)
```

---

## 3. 功能规格

### 3.1 数据层 — Hyperliquid

#### 3.1.1 `HLClient` (api.py)

**类**: `HLClient`
**职责**: 封装 Hyperliquid Info SDK，管理 HTTP 客户端实例。

**公开方法**:

```python
class HLClient:
    def __init__(self, base_url: str = constants.MAINNET_API_URL) -> None:
        """初始化，base_url 支持测试网/主网切换"""
    
    def get_meta_and_asset_ctxs(self) -> dict:
        """调用 info.meta_and_asset_ctxs()，返回全市场元数据"""
    
    def get_all_mids(self) -> dict[str, str]:
        """返回所有币当前中间价，格式 {coin: price_str}"""
    
    def get_candles(
        self,
        symbol: str,
        interval: str,  # "1h" | "4h" | "1d"
        start_time_ms: int,
        end_time_ms: int,
    ) -> list[dict]:
        """调用 info.candles_snapshot()，返回 K 线列表"""
    
    def get_funding_history(
        self,
        symbol: str,
        start_time_ms: int,
        end_time_ms: int | None = None,
    ) -> list[dict]:
        """调用 info.funding_history()"""
    
    def get_l2_snapshot(self, symbol: str) -> dict:
        """调用 info.l2_snapshot()"""
```

**异常处理**:
- 网络超时：抛出 `requests.Timeout`，由调用方重试
- HTTP 429：抛出 `ClientError`，由 tenacity 装饰器重试
- 其他错误：记录日志，返回空值/默认值

---

#### 3.1.2 `HLUtils` (utils.py)

**模块**: `hl_utils`
**职责**: 时间转换、重试、时间窗口计算。

**公开函数**:

```python
def ms_to_dt(ms: int) -> datetime:
    """毫秒 Unix → datetime（tz=UTC）"""

def dt_to_ms(dt: datetime) -> int:
    """datetime → 毫秒 Unix"""

def calc_time_range(
    interval: str,  # "1h" | "4h" | "1d"
    days: int,
    end_time_ms: int | None = None,
) -> tuple[int, int]:
    """计算时间窗口，返回 (start_ms, end_ms)
    
    规则:
    - 1h: 最近 days×24 小时
    - 4h: 最近 days×6 个 4h 周期
    - 1d: 最近 days 天
    """

@retry_on_rate_limit
def retry_call(func: Callable[..., T], *args, **kwargs) -> T:
    """指数退避重试（最多 3 次）"""
```

---

#### 3.1.3 `get_candles` (candles.py)

**函数**: `get_candles`
**签名**:
```python
def get_candles(
    symbol: str,        # "BTC" | "ETH" | "SOL"
    interval: str,      # "1h" | "4h" | "1d"
    days: int = 7,     # 向后回溯天数
) -> pd.DataFrame:
    """
    返回 DataFrame，columns:
    [timestamp, open, high, low, close, volume, n_trades]
    
    - timestamp: Unix 秒（整数）
    - 价格单位：USD（浮点数）
    - 按 timestamp 升序排列
    - 返回行数：约 days×24（1h）/ days×6（4h）/ days（1d）
    """
```

**内部调用**:
1. `HLClient.get_candles()` 获取原始数据
2. 转换为 DataFrame，统一时间戳格式
3. 查询缓存（TTL=3600s）
4. 缓存未命中则写入缓存

---

#### 3.1.4 `get_current_funding` (funding.py)

**函数**: `get_current_funding`
**签名**:
```python
def get_current_funding(symbol: str) -> dict:
    """
    返回:
    {
        "funding_rate": 0.0001,      # 8h 费率（小数，如 0.01% = 0.0001）
        "annualized": 0.1095,          # 年化费率（funding_rate × 3 × 365）
        "premium": 0.00005,            # 溢价
        "time": 1743600000,            # Unix 秒
    }
    """
```
**逻辑**: 调用 `funding_history(startTime, endTime)`，取返回列表最后一条（最新）。

---

#### 3.1.5 `get_open_interest` (oi.py)

**函数**: `get_open_interest`
**签名**:
```python
def get_open_interest(symbol: str) -> dict:
    """
    返回:
    {
        "open_interest_usd": 500_000_000.0,  # USD
        "prev_day_px": 66000.0,              # 前一日收盘价
        "mark_px": 67000.0,                  # 标记价格
        "oracle_px": 66980.0,                 # 预言机价格
        "funding": 0.0001,                    # 当前资金费率
        "day_ntl_vlm": 123_456_789.0,         # 24h 名义成交量
    }
    """
```
**重要**: `info.meta_and_asset_ctxs()` 返回 **tuple `(Meta, List[PerpAssetCtx])`**：
- 第一个元素 `Meta = {"universe": [{"name": str, "szDecimals": int}, ...]}`
- 第二个元素 `List[PerpAssetCtx]`：按 `universe` 顺序对应每个币的上下文

**逻辑**: 先从 `universe` 找到 symbol 对应的索引 `i`，再从 `asset_ctxs[i]` 提取字段。

---

#### 3.1.6 `get_orderbook` (orderbook.py)

**函数**: `get_orderbook`
**签名**:
```python
def get_orderbook(
    symbol: str,
    depth: int = 20,  # 每侧档位数
) -> dict:
    """
    返回:
    {
        "coin": "BTC",
        "time": 1743600000000,               # Unix 毫秒
        "bids": [[67000.0, 1.5], ...],       # [price, size]
        "asks": [[67100.0, 1.2], ...],
    }
    
    - bids/asks 按价格降序（最优在前）
    - 每个元素为 [price, size] 二元组
    """
```

---

#### 3.1.7 `CacheManager` (cache.py)

**类**: `CacheManager`
**职责**: SQLite 缓存管理。

**公开方法**:
```python
class CacheManager:
    def get(self, key: str) -> Any | None:
        """查找缓存，未过期返回数据，过期返回 None"""
    
    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """写入缓存，设置 TTL"""
    
    def candle_key(
        self,
        symbol: str,
        interval: str,
        start_ms: int,
        end_ms: int,
    ) -> str:
        """生成 K 线缓存 key"""
```

**缓存 TTL**:
| 数据类型 | TTL（秒） |
|---------|----------|
| K 线 | 3600（1h） |
| 资金费率 | 300（5min） |
| OI | 300（5min） |
| 订单簿 | 0（不缓存） |

---

#### 3.1.8 `get_hl_data` (main.py)

**函数**: `get_hl_data`（统一入口）
**签名**:
```python
def get_hl_data(
    symbol: str,
    date: str,                           # "YYYY-MM-DD"
    intervals: list[str] = ["1h", "4h", "1d"],
    config: dict | None = None,
    backtest_mode: bool = False,         # 回测模式标志
) -> dict:
    """
    返回聚合数据:
    {
        "symbol": "BTC",
        "candles": {
            "1h": pd.DataFrame,
            "4h": pd.DataFrame,
            "1d": pd.DataFrame,
        },
        "funding": {...},      # get_current_funding
        "open_interest": {...},# get_open_interest
        "orderbook": {...},    # get_orderbook
    }
    
    date 和 backtest_mode 参数语义:
    - backtest_mode=False（默认，实时分析）: date 仅用于记录，不做过滤
    - backtest_mode=True（回测模式）: 仅返回 timestamp <= date 的数据
    """
```

---

### 3.2 配置层

#### 3.2.1 `load_config` (config_loader.py)

**函数**: `load_config`
**签名**:
```python
def load_config(overrides: dict | None = None) -> dict:
    """加载默认配置，合并 overrides，返回深拷贝"""
```

**默认配置**:
```python
{
    "mode": "crypto",
    "project_dir": "<项目根目录>",
    "results_dir": "./results",
    "data_cache_dir": "<项目>/dataflows/hyperliquid/data_cache",
    "crypto": {
        "primary_chain": "hyperliquid",
        "supported_chains": ["hyperliquid"],
        "default_interval": "1h",
        "intervals": ["1h", "4h", "1d"],
        "max_candles_lookback_days": 7,
        "hl_api_base": "https://api.hyperliquid.xyz",
        "hl_skip_ws": True,
        "cache_ttl": {
            "candles": 3600,
            "funding": 300,
            "oi": 300,
        },
    },
    "indicators": {
        "atr_period": 14,
        "rsi_period": 14,
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        "macd_fast": 12,
        "macd_slow": 26,
        "macd_signal": 9,
        "boll_period": 20,
        "boll_std": 2,
        "volume_ma_short": 7,
        "volume_ma_long": 24,
    },
    "llm_provider": "openai",
    "deep_think_llm": "gpt-5.4",
    "quick_think_llm": "gpt-5.4-mini",
    "output_language": "English",
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
}
```

#### 3.2.2 `is_crypto_mode` (config_loader.py)

**函数**: `is_crypto_mode`
**签名**: `def is_crypto_mode(config: dict) -> bool`

---

### 3.3 技术指标层

#### 3.3.1 `compute_all_indicators` (indicators/aggregator.py)

**函数**: `compute_all_indicators`
**签名**:
```python
def compute_all_indicators(
    df: pd.DataFrame,
    config: dict | None = None,
) -> pd.DataFrame:
    """
    输入: K 线 DataFrame（timestamp, open, high, low, close, volume）
    输出: 带指标列的 DataFrame，新增列:
    - atr, rsi, macd, macd_signal, macd_hist
    - boll_upper, boll_middle, boll_lower
    - ma7, ma24, ma50, ma200
    - volume_ma7, volume_ma24
    """
```

#### 3.3.2 `get_latest_indicators` (indicators/summarizer.py)

**函数**: `get_latest_indicators`
**签名**:
```python
def get_latest_indicators(df: pd.DataFrame) -> dict:
    """
    从带指标的 DataFrame 提取最后一行，输出 dict:
    {
        "atr": float,
        "rsi": float,
        "macd": float,
        "macd_signal": float,
        "boll_upper": float,
        "boll_lower": float,
        "ma7": float,
        "ma24": float,
        "ma50": float,
        "ma200": float,
        "atr_pct": float,  # ATR / close × 100（ATR 占价格的百分比）
    }
    """
```

#### 3.3.3 Crypto 特有指标 (indicators/crypto_metrics.py)

```python
def calc_funding_rate_annualized(rate: float) -> float:
    """rate × 3 × 365"""

def calc_oi_change_rate(oi_current: float, oi_24h: float) -> float:
    """(oi_current - oi_24h) / oi_24h"""

def calc_orderbook_imbalance(bids, asks) -> float:
    """sum(bid_sizes) / sum(ask_sizes)"""

def calc_volatility_position(atr_pct: float, atr_history: list[float]) -> dict:
    """返回 {position, percentile}

    atr_history 来源：由 aggregator.py 的 compute_all_indicators() 产生，
    从 df["atr"] 列提取最近 N 条（默认 N=30）作为历史序列。
    """

def get_trend_direction(df: pd.DataFrame, ma_short=50, ma_long=200) -> str:
    """bullish | bearish | neutral"""
```

---

### 3.4 Agent 层

#### 3.4.1 `HyperliquidPerpAnalyst`

**类**: `HyperliquidPerpAnalyst`
**父类**: `CryptoBaseAnalyst`
**文件**: `agents/analysts/hyperliquid_perp_analyst.py`

**方法**: `analyze(symbol, date, data) -> dict`

**输入 data 结构**:
```python
{
    "candles": {
        "1h": pd.DataFrame,
        "4h": pd.DataFrame,
        "1d": pd.DataFrame,
    },
    "funding": {...},
    "open_interest": {...},
    "orderbook": {...},
    "indicators": dict,  # get_latest_indicators 输出
}
```

**输出 JSON schema**:
```json
{
    "summary": "string (1-2 句)",
    "direction": "bullish | bearish | neutral",
    "confidence": "float (0.0-1.0)",
    "signals": {
        "funding_rate": {
            "value": "float",
            "annualized": "float",
            "direction": "positive (longs pay) | negative (shorts pay)",
            "verdict": "normal | elevated | extreme"
        },
        "oi_trend": {
            "current": "float",
            "change_24h_pct": "float",
            "direction": "expanding | contracting | neutral",
            "verdict": "bullish | bearish | neutral"
        },
        "orderbook_imbalance": {
            "bid_depth": "float",
            "ask_depth": "float",
            "imbalance_ratio": "float",
            "verdict": "bullish | bearish | neutral"
        },
        "volume_anomaly": {
            "volume_24h": "float",
            "volume_ma7": "float",
            "ratio": "float",
            "verdict": "normal | elevated | anomalous"
        },
        "volatility": {
            "atr_24h": "float",
            "atr_pct": "float",
            "position": "low | medium | high | extreme"
        },
        "trend_4h": {
            "direction": "bullish | bearish | neutral",
            "ma_cross": "above_ma | below_ma"
        },
        "trend_1d": {
            "direction": "bullish | bearish | neutral",
            "ma_cross": "above_ma | below_ma"
        }
    },
    "metrics": {
        "mark_price": "float",
        "index_price": "float",
        "funding_rate": "float",
        "open_interest_usd": "float",
        "volume_24h": "float",
        "rsi": "float",
        "atr": "float",
        "macd": "float",
        "macd_signal": "float",
        "boll_upper": "float",
        "boll_lower": "float"
    },
    "narrative": "string (200-500 字)"
}
```

**判断阈值**（Prompt 内置，LLM 遵循）:
| Signal | 阈值 |
|--------|------|
| funding_rate verdict=elevated | 8h 费率 > 0.0001 |
| funding_rate verdict=extreme | 8h 费率 > 0.0005 |
| oi_trend verdict=expanding | 24h 变化 > 10% |
| volume_anomaly verdict=elevated | 成交量 > MA7 × 1.5 |
| volatility position=high | ATR% > 3% |
| volatility position=extreme | ATR% > 5% |

---

### 3.5 Graph 层

#### 3.5.1 `CryptoTradingAgentsGraph`

**类**: `CryptoTradingAgentsGraph`
**文件**: `graph/crypto_trading_graph.py`

**公开方法**:

```python
class CryptoTradingAgentsGraph:
    def __init__(self, config: dict) -> None:
        """初始化所有子模块"""
    
    def propagate(self, symbol: str, date: str) -> tuple[dict, str]:
        """
        端到端分析流程
        
        参数:
            symbol: "BTC" | "ETH" | "SOL"
            date: "YYYY-MM-DD"（用于回测兼容）
        
        返回:
            (analyst_report: dict, final_decision: str)
            final_decision: "long | short | hold | close"
        """
```

**子模块**:
| 模块 | 类 | 职责 |
|------|----|------|
| 数据桥接 | `HyperliquidDataBridge` | 封装 `get_hl_data` |
| 分析 | `HyperliquidPerpAnalyst` | LLM 分析 |
| 多头研究 | `BullResearcher` | 复用原项目 |
| 空头研究 | `BearResearcher` | 复用原项目 |
| 交易员 | `CryptoTraderAgent` | 汇总决策 |
| 风控 | `CryptoRiskManager` | 简化风控检查 |
| 组合管理 | `CryptoPortfolioManager` | 审批/拒绝 |

#### 3.5.2 `CryptoTraderAgent`

**输出 schema**:
```python
{
    "action": "long | short | close | hold",
    "size_pct": 0.0-1.0,        # 仓位占比
    "leverage": 1-20,            # 建议杠杆
    "entry_reason": "string",    # 入场理由
    "risk_adjusted": bool,       # 是否经过风控调整
}
```

#### 3.5.3 `CryptoRiskManager`（简化版，Phase 1）

**评估规则**:
| 规则 | 阈值 | 处理 |
|------|------|------|
| 波动率过高 | ATR% > 5% | 降低杠杆至 ≤3x |
| 订单簿极度不平衡 | ratio > 2.0 或 < 0.5 | 警告 |

---

## 4. 非功能规格

### 4.1 性能

| 指标 | 目标 |
|------|------|
| 单次 propagate() HTTP 请求数 | ≤ 10 次 |
| 数据获取响应时间 | < 5s |
| Agent 分析响应时间 | < 30s |
| 缓存命中响应时间 | < 500ms |
| 缓存命中率（第二次调用） | > 80% |

### 4.2 可靠性

- HTTP 请求失败自动重试（最多 3 次，指数退避）
- 单个子模块失败不影响整体流程（降级处理）
- 缓存 TTL 防止陈旧数据
- 回测模式数据按 `date` 过滤，无未来数据泄露

### 4.3 可维护性

- 所有函数有类型提示
- 所有公开函数/类有 Docstring
- 日志用 `logging` 模块，关键节点记录
- 不使用 `print`

---

## 5. 目录结构（Phase 1 交付时）

```
tradingagents_crypto/
├── __init__.py
├── default_config.py           # 默认配置
├── config_loader.py            # 配置加载 + 路由
│
├── dataflows/
│   ├── __init__.py
│   └── hyperliquid/
│       ├── __init__.py
│       ├── api.py             # HLClient
│       ├── utils.py           # 时间/重试工具
│       ├── candles.py         # K 线
│       ├── funding.py         # 资金费率
│       ├── oi.py              # 持仓量
│       ├── orderbook.py       # 订单簿
│       ├── cache.py           # SQLite 缓存
│       └── main.py            # get_hl_data 统一入口
│
├── indicators/
│   ├── __init__.py
│   ├── calculator.py          # ATR/RSI/MACD/Bollinger/MA
│   ├── aggregator.py           # compute_all_indicators（负责准备 atr_history）
│   ├── crypto_metrics.py       # Crypto 特有指标
│   └── summarizer.py          # get_latest_indicators
│
├── agents/
│   ├── __init__.py
│   ├── base.py                # CryptoBaseAnalyst
│   ├── schema.py              # Pydantic 模型
│   ├── validator.py           # 输出校验
│   ├── analysts/
│   │   ├── __init__.py
│   │   └── hyperliquid_perp_analyst.py
│   └── researchers/            # 复用原项目（adapter）
│
├── graph/
│   ├── __init__.py
│   ├── crypto_trading_graph.py
│   ├── data_bridge.py         # HyperliquidDataBridge
│   ├── trader_agent.py        # CryptoTraderAgent
│   ├── risk_manager.py        # CryptoRiskManager（简化）
│   └── trading_graph_factory.py
│
├── tests/                     # 测试（按类型分层）
│   ├── __init__.py
│   ├── conftest.py            # pytest fixtures
│   ├── unit/                  # 单元测试
│   │   ├── test_hl_client.py
│   │   ├── test_utils.py
│   │   ├── test_cache.py
│   │   └── test_indicators.py
│   ├── integration/           # 集成测试
│   │   ├── test_hl_integration.py
│   │   ├── test_indicators_integration.py
│   │   ├── test_analyst_integration.py
│   │   ├── test_graph_integration.py
│   │   └── test_config_integration.py
│   └── fixtures/              # Mock 数据
│       ├── mock_hl_api.py
│       ├── mock_llm.py
│       └── sample_data.py
│
├── scripts/                   # 辅助脚本
│   ├── test_hl_connection.py
│   ├── e2e_btc.py
│   ├── e2e_eth.py
│   ├── e2e_sol.py
│   └── benchmark.py
│
└── dataflows/
    └── hyperliquid/
        └── data_cache/       # SQLite 缓存目录（由 CacheManager 管理）
```

---

## 6. 依赖清单

| 依赖 | 版本 | 用途 |
|------|------|------|
| `hyperliquid-python-sdk` | >=0.3 | Hyperliquid API |
| `pandas` | >=2.0 | 数据处理 |
| `numpy` | >=1.25 | 数值计算 |
| `ta` | >=0.10 | 技术指标 |
| `requests` | >=2.31 | HTTP 客户端 |
| `tenacity` | >=8.2 | 重试逻辑 |
| `pydantic` | >=2.0 | Schema 校验 |
| `pytest` | >=7.0 | 测试 |
| `pytest-asyncio` | 最新 | 异步测试支持 |

---

## 7. 已知限制

| 限制 | 说明 | 后续版本 |
|------|------|---------|
| 不支持历史回测 | Phase 3 实现 | Phase 3 |
| 不支持 Solana 数据 | Phase 2 实现 | Phase 2 |
| 不支持 ETH 链上数据 | Phase 2 实现 | Phase 2 |
| 不执行交易 | 仅输出信号 | — |
| 不做真实 IV 分析 | 用 HV 替代 | Phase 3 可选 |
| Hyperliquid SDK Python 3.10 限制 | 独立虚拟环境隔离 | — |

---

## 8. 验收检查表

### 8.1 数据层
- [ ] `get_candles("BTC", "1h", 7)` 返回 ~168 条 DataFrame
- [ ] `get_candles("ETH", "4h", 7)` 返回 ~42 条 DataFrame
- [ ] `get_current_funding("BTC")` 返回 `{funding_rate, annualized, premium, time}`
- [ ] `get_open_interest("BTC")` 返回 `{open_interest_usd, mark_px, ...}`
- [ ] `get_orderbook("BTC")` 返回 `{bids, asks}`
- [ ] 缓存命中时响应 < 500ms
- [ ] `get_hl_data("BTC", "2026-03-25")` 按 date 正确过滤

### 8.2 指标层
- [ ] `compute_all_indicators(df)` 包含所有指标列
- [ ] ATR / RSI / MACD 计算正确
- [ ] `get_latest_indicators(df)` 输出完整 dict
- [ ] `calc_orderbook_imbalance` 正确处理空列表

### 8.3 Agent 层
- [ ] `analyze()` 返回完整 JSON
- [ ] JSON 包含所有必填字段
- [ ] `direction` 在 `bullish | bearish | neutral` 之中
- [ ] `confidence` 在 0.0-1.0 范围
- [ ] Pydantic schema 校验通过

### 8.4 Graph 层
- [ ] `propagate("BTC", "2026-03-25")` 返回 tuple(dict, str)
- [ ] `final_decision` 在 `long | short | hold | close` 之中
- [ ] `create_graph(config)` 根据 mode 返回正确实例

### 8.5 集成
- [ ] BTC / ETH / SOL 三币种全部跑通
- [ ] 单次 propagate() HTTP ≤ 10 次
- [ ] 回测模式无未来数据泄露
- [ ] API 限流时重试成功

---

*本规格说明书为 Phase 1 开发、测试和验收的基准文件。任何变更需更新本文件。*
