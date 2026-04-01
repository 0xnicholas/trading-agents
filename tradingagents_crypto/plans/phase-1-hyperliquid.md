# Phase 1：Hyperliquid 单链打样

**周期**: 2-3 周
**目标**: 跑通完整的 Crypto 版 TradingAgents pipeline，以 Hyperliquid 为单一数据源
**SDK 验证**: ✅ 已完成（见 `../docs/sdk_findings.md`）

---

## 里程碑

### M1.0：SDK 探测验证（Day 1）
- [ ] 克隆 `hyperliquid-python-sdk` 源码
- [ ] 验证所有 Info API 端点（`meta_and_asset_ctxs`, `l2_snapshot`, `candles_snapshot`, `funding_history`）
- [ ] 确认各端点返回数据结构和字段名
- [ ] 验证时间戳格式（ms vs 秒）
- [ ] 输出：`docs/sdk_findings.md`

### M1.1：环境搭建（Day 1-2）
- [ ] 创建独立虚拟环境 `tradingagents-crypto`（Python 3.10）
- [ ] 安装核心依赖：
  ```toml
  hyperliquid-python-sdk = "^0.3"
  pandas = "^2.0"
  numpy = "^1.25"
  ta = "^0.10"          # 技术指标（替代 stockstats）
  requests = "^2.31"
  tenacity = "^8.2"     # 重试逻辑
  pydantic = "^2.0"      # Schema 校验
  ```
- [ ] 创建包目录结构（与 AGENTS.md 一致）
- [ ] 验证 SDK 连接：`Info(skip_ws=True)` → `all_mids()` 返回价格字典

### M1.2：数据层（Day 2-6）

#### 目录结构
```
dataflows/hyperliquid/
├── __init__.py
├── api.py              # SDK 封装基类（Info 客户端管理）
├── utils.py            # 时间转换 / 重试 / 缓存工具
├── candles.py          # K 线数据（1h / 4h / 1d）
├── funding.py          # 资金费率（当前 + 历史）
├── oi.py               # 持仓量（从 meta_and_asset_ctxs 提取）
├── orderbook.py        # 订单簿（l2_snapshot）
├── trades.py           # 成交（candles 内含 n=成交笔数）
└── main.py             # 统一入口，对齐 y_finance.py 接口
```

#### 核心函数签名（已验证）

```python
# candles.py
def get_candles(
    symbol: str,           # "BTC", "ETH"（不需要 "-PERP"）
    interval: str,         # "1h" | "4h" | "1d"
    start_time_ms: int,    # Unix 毫秒
    end_time_ms: int,      # Unix 毫秒
) -> pd.DataFrame:        # columns: [timestamp, open, high, low, close, volume]

# funding.py
def get_current_funding(symbol: str) -> dict:
    # 内部调用 funding_history(startTime, endTime) 取最近一条
    # 返回: {funding_rate, annualized, premium, time}

def get_funding_history(
    symbol: str,
    start_time_ms: int,
    end_time_ms: int,
) -> list[dict]:  # [{coin, fundingRate, premium, time}, ...]

# oi.py
def get_open_interest(symbol: str) -> dict:
    # 从 meta_and_asset_ctxs() 提取当前 symbol 的 openInterest
    # 返回: {open_interest_usd, prev_day_px, mark_px, oracle_px}

# orderbook.py
def get_orderbook(symbol: str, depth: int = 20) -> dict:
    # 调用 l2_snapshot(name)
    # 返回: {coin, bids: [(px, sz)], asks: [(px, sz)], time}
```

#### SQLite 缓存策略
- 缓存文件：`{cache_dir}/{symbol}_{interval}_{start_ms}_{end_ms}.db`
- K 线缓存 TTL：1 小时
- 资金费率/OI 缓存 TTL：5 分钟
- 回测过滤：所有数据按 `curr_date` 过滤（`timestamp <= curr_date`）

### M1.3：配置层（Day 3-4）
- [ ] `default_config.py` — Crypto 专用配置
  ```python
  config = {
      "mode": "crypto",
      "crypto": {
          "primary_chain": "hyperliquid",
          "default_interval": "1h",
          "intervals": ["1h", "4h", "1d"],
          "max_candles_lookback_days": 7,
          "hl_api_base": "https://api.hyperliquid.xyz",
          "hl_skip_ws": True,
      },
      # 技术指标配置
      "indicators": {
          "atr_period": 14,
          "rsi_period": 14,
          "rsi_overbought": 70,
          "rsi_oversold": 30,
      },
  }
  ```
- [ ] `mode="crypto"` 路由判断（`config["mode"] == "crypto"` → `CryptoTradingGraph`）

### M1.4：技术指标计算（Day 4-5）
- [ ] `indicators.py` — 使用 `ta` 库计算技术指标（替代原 `stockstats`）
  - ATR（14 周期）
  - RSI（14 周期）
  - MACD（12/26/9）
  - Bollinger Bands（20 周期，2 标准差）
  - 成交量均线（MA7 / MA24）
- [ ] OI 变化率计算：`OI_t / OI_{t-24h} - 1`
- [ ] 订单簿多空不平衡度：`sum(bid_depth) / sum(ask_depth)`
- [ ] 波动率位置判断（ATR 百分位）

### M1.5：Agent 层（Day 6-10）

#### `agents/base.py` — Crypto 基础 Analyst 类
```python
class CryptoBaseAnalyst(BaseModel):
    config: dict
    llm_provider: str
    deep_think_llm: str
    quick_think_llm: str

    def analyze(self, symbol: str, date: str) -> dict:
        """返回符合 schema 的 JSON"""
        ...
```

#### `agents/analysts/hyperliquid_perp_analyst.py`

**Prompt 核心逻辑**：
```
你是一个 Hyperliquid 永续合约数据分析师。
给定以下数据：
- K 线（1h / 4h / 1d）
- 当前资金费率：{funding_rate}（年化 {annualized_rate}）
- 订单簿多空比：{ob_imbalance}
- OI 24h 变化：{oi_change_pct}%
- ATR 波动率位置：{atr_position}
- 成交量异常度：{volume_anomaly}

请输出 JSON：
{
    "summary": "短期偏多/偏空/中性，核心理由（1-2句）",
    "direction": "bullish | bearish | neutral",
    "confidence": 0.0-1.0,
    "signals": {...},      # 见下方详表
    "metrics": {...},      # 原始数值
    "narrative": "详细分析（200-500字，供 Researcher 辩论）"
}
```

**signals 输出定义**：

| Signal | 判断逻辑 | verdict |
|--------|---------|---------|
| `funding_rate` | >0.01%（8h）为 elevated，>0.05% 为 extreme | normal / elevated / extreme |
| `oi_trend` | OI 变化率 >10% 为极端膨胀 | expanding / contracting / neutral |
| `orderbook_imbalance` | ratio >1.2 或 <0.8 为显著偏多/空 | bullish / bearish / neutral |
| `volume_anomaly` | 成交量 >MA7×1.5 为异常 | normal / elevated / anomalous |
| `volatility` | ATR% >3% 为高波动，>5% 为极端 | low / medium / high / extreme |
| `trend_4h` | 4h MA 方向 | bullish / bearish / neutral |
| `trend_1d` | 1d MA 方向 | bullish / bearish / neutral |

### M1.6：Graph 集成（Day 11-15）

#### `graph/crypto_trading_graph.py`

**关键设计**：复用原 `tradingagents/graph/` 的 `setup.py`、`propagation.py`、`reflection.py`，只替换 `TradingAgentsGraph` 为 `CryptoTradingAgentsGraph`。

```python
class CryptoTradingAgentsGraph:
    def __init__(self, config: dict):
        self.config = config
        self.analyst = HyperliquidPerpAnalyst(config)  # 替换原 FundamentalsAnalyst
        self.researcher = ...  # 复用原 Bull/Bear Researcher
        self.trader = CryptoTraderAgent(config)        # 扩展 Trader
        self.risk_mgmt = CryptoRiskManager(config)     # 扩展风控
        self.portfolio_manager = PortfolioManager(config)

    def propagate(self, symbol: str, date: str) -> tuple[dict, str]:
        # 1. 获取三周期 K 线
        candles_1h = get_candles(symbol, "1h", ...)
        candles_4h = get_candles(symbol, "4h", ...)
        candles_1d = get_candles(symbol, "1d", ...)

        # 2. 获取 funding / OI / orderbook
        funding = get_current_funding(symbol)
        oi = get_open_interest(symbol)
        ob = get_orderbook(symbol)

        # 3. 计算技术指标
        indicators = calc_indicators(candles_1h)

        # 4. Analyst 输出
        analyst_report = self.analyst.analyze(symbol, date, {
            "candles": {"1h": candles_1h, "4h": candles_4h, "1d": candles_1d},
            "funding": funding,
            "oi": oi,
            "orderbook": ob,
            "indicators": indicators,
        })

        # 5. Researcher 辩论
        bull_case = self.bull_researcher.research(analyst_report)
        bear_case = self.bear_researcher.research(analyst_report)

        # 6. Trader 汇总
        decision = self.trader.decide(symbol, analyst_report, bull_case, bear_case)

        # 7. Risk 评估
        risk_report = self.risk_mgmt.evaluate(decision)

        # 8. Portfolio Manager 审批
        final_decision = self.portfolio_manager.approve(decision, risk_report)

        return final_decision
```

### M1.7：端到端测试（Day 16-21）

| 测试用例 | 验收条件 |
|---------|---------|
| `propagate("BTC", "2026-03-25")` | 返回完整 JSON 报告 |
| `propagate("ETH", "2026-03-25")` | 同上 |
| `propagate("SOL", "2026-03-25")` | 同上 |
| 回测模式（`curr_date=2026-03-20`） | 数据不包含 3-21 及之后 |
| 第二次相同调用 | 走缓存，< 500ms |
| API 限流降级 | 单次失败后自动重试，成功返回 |

---

## API 调用分析（已验证）

单次 `propagate()` 最小 HTTP 调用数：**5 次**

| 数据 | 端点 | 次数 |
|------|------|------|
| 元数据 + OI + funding（所有币） | `meta_and_asset_ctxs()` | 1 |
| BTC 订单簿 | `l2_snapshot("BTC")` | 1 |
| BTC K 线 1h | `candles_snapshot("BTC", "1h", start, end)` | 1 |
| BTC K 线 4h | `candles_snapshot("BTC", "4h", start, end)` | 1 |
| BTC K 线 1d | `candles_snapshot("BTC", "1d", start, end)` | 1 |
| **合计** | | **5 次** |

加上容错重试（×2）< **10 次**，远低于原计划 20 次上限。

---

## 修订说明（相比初版）

| # | 初版问题 | 修订后 |
|---|---------|--------|
| 1 | API 端点名称猜测 | ✅ 已验证：`candles_snapshot`, `l2_snapshot`, `meta_and_asset_ctxs`, `funding_history` |
| 2 | 目录结构混乱 | ✅ 统一为 `dataflows/hyperliquid/` 子模块 |
| 3 | symbol 格式未定义 | ✅ 明确 `"BTC"` 格式，不需要 `-PERP` |
| 4 | K 线多周期返回方式 | ✅ 三个独立函数或统一 `get_candles(interval)` |
| 5 | 技术指标库 | ✅ 明确用 `ta` 库替代 `stockstats` |
| 6 | Graph 路由逻辑 | ✅ M1.6 给出伪代码 |
| 7 | M1.3 时间重叠 | ✅ 配置提到 M1.3（Day 3-4），与技术指标并行 |
| 8 | 缺少 SDK 验证里程碑 | ✅ 新增 M1.0 |

---

## 风险与缓解（更新）

| 风险 | 影响 | 缓解 |
|------|------|------|
| `meta_and_asset_ctxs()` 返回全市场 OI（字符串），需解析 | 数据格式不确定 | M1.0 验证响应格式 |
| `candles_snapshot` 时间窗口计算复杂 | 实现容易出错 | M1.2 写工具函数 `calc_time_range(symbol, interval, days)` |
| 资金费率年化计算：8h 一次 × 3 次/天 × 365 天 | 需确认公式 | 公式：`(funding_rate × 3 × 365)` |
| SDK 内部 `name_to_coin` 映射不包含PERP币 | 传入 "BTC-PERP" 失败 | 约定：只用币种名如 `"BTC"`，SDK 内部处理 |

---

*Phase 1 完成后，数据层和 Agent 框架稳定，再启动 Phase 2。*
