# M1.5：Agent 层

**状态**: 🔵 就绪（未开始）
**周期**: Day 6-10
**前置依赖**: M1.2 ✅（数据层）+ M1.3 ✅（配置）+ M1.4 ✅（指标）

---

## 任务目标

实现 `HyperliquidPerpAnalyst` Agent，接收 K 线/资金费率/OI/订单簿/指标数据，输出结构化分析 JSON。同时接入原项目的 `Bull/Bear Researcher`。

---

## 详细子任务

### T1.5.1 `agents/base.py` — Crypto 基础 Analyst 类
- [ ] 创建 `CryptoBaseAnalyst` 基类
  ```python
  from abc import ABC, abstractmethod
  from typing import Any
  
  class CryptoBaseAnalyst(ABC):
      def __init__(self, config: dict):
          self.config = config
          self.llm_provider = config.get("llm_provider", "openai")
          self.deep_think_llm = config.get("deep_think_llm")
          self.quick_think_llm = config.get("quick_think_llm")
      
      @abstractmethod
      def analyze(self, symbol: str, date: str, data: dict) -> dict:
          """核心分析方法，返回结构化 JSON"""
          pass
      
      def _call_llm(self, prompt: str, model: str = None) -> str:
          """调用 LLM（复用原项目 llm_clients）"""
          # 复用 tradingagents.llm_clients
          ...
  ```

### T1.5.2 `agents/analysts/hyperliquid_perp_analyst.py` — 核心 Analyst
- [ ] `HyperliquidPerpAnalyst` 类
  - 接收数据：candles / funding / oi / orderbook / indicators
  - 调用 LLM 生成分析
  - 输出结构化 JSON

- [ ] Prompt 工程：
  ```python
  SYSTEM_PROMPT = """你是一个 Hyperliquid 永续合约数据分析师。
  
  你是专业的加密货币永续合约分析师，专注于 Hyperliquid 交易所。
  你的任务是分析 K 线数据、资金费率、持仓量（OI）、订单簿深度和技术指标，
  给出客观、专业、有据可查的交易参考意见。
  
  输出格式：严格 JSON，不做任何额外解释。
  """

  USER_PROMPT_TEMPLATE = """
  ## 当前分析标的
  - 交易对：{symbol}-PERP（Hyperliquid 永续合约）
  - 分析日期：{date}
  
  ## K 线数据（1h，主分析周期）
  最新收盘价：{close_1h}
  1h 涨跌：{change_1h_pct}%
  成交量：{volume_1h}（24h）
  
  ## 4h K 线摘要
  收盘价：{close_4h}，趋势：{trend_4h}
  
  ## 1d K 线摘要
  收盘价：{close_1d}，趋势：{trend_1d}
  
  ## 资金费率
  当前 8h 费率：{funding_rate}（年化 {annualized_rate}）
  费率方向：{funding_direction}（多头支付/空头支付）
  评级：{funding_verdict}（正常/偏高/极端）
  
  ## 持仓量（Open Interest）
  当前 OI：${oi_usd}
  24h 变化：{oi_change_pct}%
  评级：{oi_verdict}（膨胀/收缩/中性）
  
  ## 订单簿深度
  多空不平衡度：{ob_imbalance}（>1 偏多，<1 偏空）
  评级：{ob_verdict}（偏多/偏空/中性）
  
  ## 技术指标
  - RSI(14)：{rsi}（{'超买' if rsi>70 else '超卖' if rsi<30 else '中性'}）
  - ATR(14)：{atr}（{atr_pct}%）
  - 波动率位置：{vol_position}
  - MACD：{macd}，信号线：{macd_signal}，柱状图：{macd_hist}
  
  请输出 JSON（严格按照以下 schema）：
  {{
      "summary": "短期偏多/偏空/中性，核心理由（1-2句）",
      "direction": "bullish | bearish | neutral",
      "confidence": 0.0-1.0,
      "signals": {{
          "funding_rate": {{
              "value": {funding_rate},
              "annualized": {annualized_rate},
              "direction": "positive (longs pay) | negative (shorts pay)",
              "verdict": "normal | elevated | extreme"
          }},
          "oi_trend": {{
              "current": {oi_usd},
              "change_24h_pct": {oi_change_pct},
              "direction": "expanding | contracting | neutral",
              "verdict": "bullish | bearish | neutral"
          }},
          "orderbook_imbalance": {{
              "bid_depth": {bid_depth},
              "ask_depth": {ask_depth},
              "imbalance_ratio": {ob_imbalance},
              "verdict": "bullish | bearish | neutral"
          }},
          "volume_anomaly": {{
              "volume_24h": {volume_24h},
              "volume_ma7": {volume_ma7},
              "ratio": {volume_ratio},
              "verdict": "normal | elevated | anomalous"
          }},
          "volatility": {{
              "atr_24h": {atr},
              "atr_pct": {atr_pct},
              "position": "low | medium | high | extreme"
          }},
          "trend_4h": {{
              "direction": "bullish | bearish | neutral",
              "ma_cross": "above_ma | below_ma"
          }},
          "trend_1d": {{
              "direction": "bullish | bearish | neutral",
              "ma_cross": "above_ma | below_ma"
          }}
      }},
      "metrics": {{
          "mark_price": {mark_price},
          "index_price": {index_price},
          "funding_rate": {funding_rate},
          "open_interest_usd": {oi_usd},
          "volume_24h": {volume_24h},
          "rsi": {rsi},
          "atr": {atr},
          "macd": {macd},
          "macd_signal": {macd_signal},
          "boll_upper": {boll_upper},
          "boll_lower": {boll_lower}
      }},
      "narrative": "详细分析（200-500字），包含对各信号的深入解读，供研究员辩论使用。"
  }}
  """
  ```

### T1.5.3 Prompt 调优
- [ ] 初始 Prompt 编写完成
- [ ] 测试 `analyze("BTC", "2026-03-25", data_dict)` 返回 JSON
- [ ] 验证 JSON schema 完整性（所有字段存在）
- [ ] 调优方向：
  - LLM 有时会漏字段 → 强化 prompt 中的 schema 说明
  - narrative 太短 → 增加字数要求
  - confidence 不合理 → prompt 增加评分标准

### T1.5.4 接入 Bull/Bear Researcher
- [ ] 研究原项目 `BullResearcher` / `BearResearcher` 接口
- [ ] 创建 `tradingagents_crypto/agents/researchers/` 目录
- [ ] 复用或继承原 Researcher：
  ```python
  from tradingagents.agents.researchers.bull_researcher import BullResearcher
  from tradingagents.agents.researchers.bear_researcher import BearResearcher
  ```
- [ ] 如果原接口不兼容，创建适配器 `ResearcherAdapter`

### T1.5.5 输出 Schema 验证
- [ ] `agents/schema.py` — Pydantic 模型定义
  ```python
  from pydantic import BaseModel, Field
  
  class FundingSignal(BaseModel):
      value: float
      annualized: float
      direction: str
      verdict: str  # normal | elevated | extreme
  
  class HyperliquidPerpSignals(BaseModel):
      funding_rate: FundingSignal
      oi_trend: dict
      orderbook_imbalance: dict
      volume_anomaly: dict
      volatility: dict
      trend_4h: dict
      trend_1d: dict
  
  class HyperliquidPerpReport(BaseModel):
      summary: str
      direction: str  # bullish | bearish | neutral
      confidence: float = Field(ge=0.0, le=1.0)
      signals: HyperliquidPerpSignals
      metrics: dict
      narrative: str
  ```
- [ ] `agents/validator.py` — 输出校验
  - LLM 返回后用 Pydantic 校验
  - 字段缺失时降级处理（使用默认值，不崩溃）

### T1.5.6 Agent 单元测试
- [ ] `tests/test_hyperliquid_analyst.py`
  - Mock LLM 返回（避免真实 API 调用）
  - Mock 数据层（避免真实 HTTP 请求）
  - 验证输出 schema 合规
  - 验证 direction 字段在 bullish/bearish/neutral 之中

---

## 交付物

| 文件 | 说明 |
|------|------|
| `agents/base.py` | Crypto 基础 Analyst 类 |
| `agents/analysts/hyperliquid_perp_analyst.py` | 永续合约分析师 |
| `agents/schema.py` | Pydantic 输出模型 |
| `agents/validator.py` | 输出校验器 |
| `agents/researchers/` | Researcher 复用/适配 |
| `tests/test_hyperliquid_analyst.py` | Agent 测试 |

---

## 验收标准

- [ ] `HyperliquidPerpAnalyst().analyze()` 返回完整 JSON
- [ ] JSON 包含 `summary` / `direction` / `signals` / `metrics` / `narrative`
- [ ] `direction` 值在 `bullish | bearish | neutral` 之中
- [ ] `confidence` 在 0.0-1.0 范围
- [ ] 所有 signals 子字段存在
- [ ] Mock 测试全部通过
- [ ] Pydantic schema 校验通过

---

## 预计工时

| 子任务 | 预计时间 |
|--------|---------|
| T1.5.1 base.py | 1 小时 |
| T1.5.2 analyst.py | 4 小时（Prompt 工程重点） |
| T1.5.3 Prompt 调优 | 4 小时（迭代调优） |
| T1.5.4 Researcher 接入 | 2 小时 |
| T1.5.5 Schema 验证 | 2 小时 |
| T1.5.6 测试 | 2 小时 |
| **合计** | **~15 小时（3 天）** |
