# M1.4：技术指标计算

**状态**: 🔵 就绪（未开始）
**周期**: Day 4-5
**前置依赖**: M1.2 ✅（需要 candles DataFrame）

---

## 任务目标

实现 `indicators.py`，使用 `ta` 库计算 Crypto 永续合约特有的技术指标，输出标准化格式供 Agent 使用。

---

## 详细子任务

### T1.4.1 基础指标计算
- [ ] `indicators/calculator.py` — 核心计算函数
  ```python
  import ta
  import pandas as pd
  
  def calc_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
      """计算 ATR（Average True Range）"""
      high = df['high']
      low = df['low']
      close = df['close']
      tr = ta.volatility.true_range(high, low, close)
      return ta.volatility.avg_true_range(high, low, close, window=period)
  
  def calc_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
      """计算 RSI"""
      return ta.momentum.RSIIndicator(df['close'], window=period).rsi()
  
  def calc_macd(
      df: pd.DataFrame,
      fast: int = 12,
      slow: int = 26,
      signal: int = 9
  ) -> dict[str, pd.Series]:
      """计算 MACD，返回 {macd, signal, histogram}"""
      macd = ta.trend.MACD(
          df['close'],
          window_fast=fast,
          window_slow=slow,
          window_sign=signal
      )
      return {
          "macd": macd.macd(),
          "signal": macd.macd_signal(),
          "histogram": macd.macd_diff(),
      }
  
  def calc_bollinger_bands(
      df: pd.DataFrame,
      period: int = 20,
      std_dev: int = 2
  ) -> dict[str, pd.Series]:
      """计算布林带，返回 {upper, middle, lower}"""
      boll = ta.volatility.BollingerBands(
          df['close'],
          window=period,
          window_dev=std_dev
      )
      return {
          "upper": boll.bollinger_hband(),
          "middle": boll.bollinger_mavg(),
          "lower": boll.bollinger_lband(),
      }
  
  def calc_ma(df: pd.DataFrame, periods: list[int] = [7, 24, 50, 200]) -> dict[str, pd.Series]:
      """计算多条均线"""
      return {f"ma{p}": ta.trend.SMAIndicator(df['close'], window=p).sma_indicator()
              for p in periods}
  ```

### T1.4.2 聚合指标计算
- [ ] `indicators/aggregator.py` — 输入 K 线 DataFrame，输出完整指标
  ```python
  def compute_all_indicators(
      df: pd.DataFrame,
      config: dict = None
  ) -> pd.DataFrame:
      """计算所有指标，返回带指标的 DataFrame"""
      config = config or {}
      period = config.get("atr_period", 14)
      # ... 依次计算所有指标
      return df
  ```

### T1.4.3 Crypto 特有指标
- [ ] `indicators/crypto_metrics.py` — Crypto 特有指标
  ```python
  def calc_funding_rate_annualized(funding_rate: float) -> float:
      """资金费率年化 = rate × 3 × 365"""
      return funding_rate * 3 * 365
  
  def calc_oi_change_rate(oi_current: float, oi_24h_ago: float) -> float:
      """OI 变化率 = (current - 24h_ago) / 24h_ago"""
      if oi_24h_ago == 0:
          return 0.0
      return (oi_current - oi_24h_ago) / oi_24h_ago
  
  def calc_orderbook_imbalance(
      bids: list[list[float]],   # [[price, size], ...]
      asks: list[list[float]],
  ) -> float:
      """订单簿多空不平衡度 = sum(bid_sizes) / sum(ask_sizes)"""
      bid_depth = sum(s for _, s in bids)
      ask_depth = sum(s for _, s in asks)
      if ask_depth == 0:
          return 1.0
      return bid_depth / ask_depth
  
  def calc_volume_anomaly(
      volume_current: float,
      volume_ma: float,
      threshold: float = 1.5
  ) -> dict:
      """成交量异常检测"""
      ratio = volume_current / volume_ma if volume_ma > 0 else 0
      return {
          "ratio": ratio,
          "is_anomaly": ratio > threshold,
          "label": "elevated" if ratio > threshold else "normal"
      }
  
  def calc_volatility_position(
      atr_pct: float,
      atr_history: list[float],
  ) -> dict:
      """ATR 波动率位置判断"""
      if not atr_history:
          return {"position": "unknown", "percentile": None}
      # 当前 ATR 在历史 ATR 序列中的百分位
      percentile = sum(1 for v in atr_history if v < atr_pct) / len(atr_history)
      if percentile > 0.9:
          position = "extreme_high"
      elif percentile > 0.7:
          position = "high"
      elif percentile > 0.3:
          position = "medium"
      else:
          position = "low"
      return {"position": position, "percentile": percentile}
  ```

### T1.4.4 指标摘要提取
- [ ] `indicators/summarizer.py` — 从指标 DataFrame 提取最新值（用于 Agent 输入）
  ```python
  def get_latest_indicators(df: pd.DataFrame) -> dict:
      """从带指标的 DataFrame 提取最新行，输出 dict"""
      latest = df.iloc[-1]
      return {
          "atr": float(latest.get("atr", 0)),
          "rsi": float(latest.get("rsi", 50)),
          "macd": float(latest.get("macd", 0)),
          "macd_signal": float(latest.get("macd_signal", 0)),
          "boll_upper": float(latest.get("boll_upper", 0)),
          "boll_lower": float(latest.get("boll_lower", 0)),
          "ma7": float(latest.get("ma7", 0)),
          "ma24": float(latest.get("ma24", 0)),
          "ma50": float(latest.get("ma50", 0)),
          "ma200": float(latest.get("ma200", 0)),
      }
  
  def get_trend_direction(df: pd.DataFrame, ma_short: int = 50, ma_long: int = 200) -> str:
      """基于 MA 交叉判断趋势方向"""
      latest = df.iloc[-1]
      ma_s = latest.get(f"ma{ma_short}", 0)
      ma_l = latest.get(f"ma{ma_long}", 0)
      if ma_s > ma_l:
          return "bullish"
      elif ma_s < ma_l:
          return "bearish"
      return "neutral"
  ```

### T1.4.5 指标单元测试
- [ ] `tests/test_indicators.py`
  - Mock K 线 DataFrame，验证 ATR/RSI/MACD 计算正确性
  - 验证布林带计算（上下轨 = 中轨 ± 2×标准差）
  - 验证订单簿不平衡度计算

---

## 交付物

| 文件 | 说明 |
|------|------|
| `indicators/calculator.py` | ATR / RSI / MACD / Bollinger / MA |
| `indicators/aggregator.py` | 聚合计算入口 |
| `indicators/crypto_metrics.py` | Crypto 特有指标 |
| `indicators/summarizer.py` | 最新值提取 |
| `tests/test_indicators.py` | 指标计算测试 |

---

## 验收标准

- [ ] ATR 计算结果与 stockstats 一致（误差 < 0.01）
- [ ] RSI 计算结果与 TradingView 一致（误差 < 0.1）
- [ ] `calc_orderbook_imbalance` 正确处理空列表
- [ ] `calc_volatility_position` 在 percentile > 90% 时返回 `"extreme_high"`
- [ ] `compute_all_indicators` 返回的 DataFrame 包含所有指标列
- [ ] Mock 测试全部通过

---

## 依赖

- `ta >= 0.10`
- `pandas >= 2.0`
- `numpy >= 1.25`

---

## 预计工时

| 子任务 | 预计时间 |
|--------|---------|
| T1.4.1 基础指标 | 2 小时 |
| T1.4.2 聚合计算 | 1 小时 |
| T1.4.3 Crypto 特有 | 2 小时 |
| T1.4.4 摘要提取 | 1 小时 |
| T1.4.5 测试 | 2 小时 |
| **合计** | **~8 小时（1.5 天）** |
