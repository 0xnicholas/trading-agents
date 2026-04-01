# M1.2：数据层

**状态**: 🔵 就绪（未开始）
**周期**: Day 2-6
**前置依赖**: M1.1 ✅

---

## 任务目标

实现 `dataflows/hyperliquid/` 完整数据层，封装 SDK 端点，提供统一的 Python 接口，对齐原 `y_finance.py` 的函数风格。

---

## 详细子任务

### T1.2.1 `hyperliquid/api.py` — SDK 客户端封装
- [ ] 创建 `HLClient` 类，管理 `Info` 实例
  ```python
  class HLClient:
      def __init__(self, base_url: str = constants.MAINNET_API_URL):
          self.info = Info(base_url, skip_ws=True)
      
      def get_meta_and_asset_ctxs(self) -> dict:
          """获取全市场元数据 + 资产上下文（全能接口）"""
          return self.info.meta_and_asset_ctxs()
      
      def get_all_mids(self) -> dict[str, str]:
          """获取所有币中间价"""
          return self.info.all_mids()
  ```
- [ ] 实现单例模式或全局客户端复用
- [ ] 添加基础错误处理（网络异常、超时）

### T1.2.2 `hyperliquid/utils.py` — 工具函数
- [ ] `ms_to_dt(ms: int) -> datetime` — 毫秒转 datetime
- [ ] `dt_to_ms(dt: datetime) -> int` — datetime 转毫秒
- [ ] `calc_time_range(interval: str, days: int) -> tuple[int, int]` — 计算时间窗口
  - 输入 `"1h", 7` → 输出 `(start_ms, end_ms)`（最近 7 天）
  - 输入 `"4h", 7` → 同上
  - 输入 `"1d", 30` → 输出 `(start_ms, end_ms)`（最近 30 天）
- [ ] `retry_on_rate_limit(func, max_retries=3)` — 基于 tenacity 的重试装饰器

### T1.2.3 `hyperliquid/candles.py` — K 线数据
- [ ] `get_candles(symbol: str, interval: str, days: int = 7) -> pd.DataFrame`
  - `interval`: `"1h"` | `"4h"` | `"1d"`
  - 返回 DataFrame，columns：`[timestamp, open, high, low, close, volume, n_trades]`
  - 内部调用 `candles_snapshot(name, interval, startTime, endTime)`
  - 时间戳统一转换为 **Unix 秒**（整数）
  - 按 `timestamp` 升序排列
- [ ] `get_candles_batch(symbols: list[str], interval: str, days: int) -> dict[str, pd.DataFrame]`
  - 批量获取多币种 K 线

### T1.2.4 `hyperliquid/funding.py` — 资金费率
- [ ] `get_current_funding(symbol: str) -> dict`
  ```python
  {
      "funding_rate": 0.0001,        # 8h 费率（小数）
      "annualized": 0.1095,           # 年化（×3×365）
      "premium": 0.00005,
      "time": 1743600000,             # Unix 秒
  }
  ```
  - 内部调用 `funding_history(symbol, startTime, endTime)` 取最近一条
- [ ] `get_funding_history(symbol: str, days: int = 30) -> list[dict]`
  - 返回历史资金费率列表

### T1.2.5 `hyperliquid/oi.py` — 持仓量
- [ ] `get_open_interest(symbol: str) -> dict`
  ```python
  {
      "open_interest_usd": 500_000_000.0,
      "prev_day_px": 66000.0,
      "mark_px": 67000.0,
      "oracle_px": 66980.0,
      "funding": 0.0001,
      "day_ntl_vlm": 123_456_789.0,
  }
  ```
  - 从 `meta_and_asset_ctxs()` 提取对应 symbol 的数据
  - `open_interest` 是 USD 字符串，需转换为 float

### T1.2.6 `hyperliquid/orderbook.py` — 订单簿
- [ ] `get_orderbook(symbol: str, depth: int = 20) -> dict`
  ```python
  {
      "coin": "BTC",
      "time": 1743600000000,         # Unix 毫秒
      "bids": [[67000.0, 1.5], [66900.0, 2.3], ...],  # [price, size]
      "asks": [[67100.0, 1.2], [67200.0, 0.8], ...],
  }
  ```
  - 内部调用 `l2_snapshot(name)`
  - `depth` 参数控制每侧返回档位数量
  - bid/ask 按价格降序排列

### T1.2.7 `hyperliquid/cache.py` — SQLite 缓存
- [ ] `CacheManager` 类
  ```python
  class CacheManager:
      def __init__(self, cache_dir: str = "./data_cache"):
          self.cache_dir = cache_dir
          os.makedirs(cache_dir, exist_ok=True)
      
      def get(self, key: str) -> Any | None:
          """根据 key 查找缓存，未过期返回数据"""
      
      def set(self, key: str, value: Any, ttl_seconds: int):
          """写入缓存，设置 TTL"""
      
      def candle_key(self, symbol: str, interval: str, start_ms: int, end_ms: int) -> str:
          return f"hl_candle_{symbol}_{interval}_{start_ms}_{end_ms}"
  ```
- [ ] K 线缓存 TTL：3600 秒（1 小时）
- [ ] 资金费率/OI 缓存 TTL：300 秒（5 分钟）
- [ ] 订单簿不缓存（实时数据）

### T1.2.8 `hyperliquid/main.py` — 统一入口
- [ ] `get_hl_data(symbol: str, date: str, intervals: list[str] = ["1h", "4h", "1d"]) -> dict`
  - 对外统一接口，聚合所有数据
  - 日期格式：`"YYYY-MM-DD"`（用于回测兼容，按 `curr_date` 过滤）
  ```python
  {
      "symbol": "BTC",
      "candles": {
          "1h": pd.DataFrame,
          "4h": pd.DataFrame,
          "1d": pd.DataFrame,
      },
      "funding": {...},
      "open_interest": {...},
      "orderbook": {...},
  }
  ```

### T1.2.9 单元测试
- [ ] `tests/test_candles.py` — Mock HTTP 响应，验证 K 线解析
- [ ] `tests/test_funding.py` — Mock funding_history 响应
- [ ] `tests/test_oi.py` — Mock meta_and_asset_ctxs 响应
- [ ] `tests/test_orderbook.py` — Mock l2_snapshot 响应
- [ ] `tests/test_cache.py` — 缓存读写 + TTL 过期

---

## 交付物

| 文件 | 说明 |
|------|------|
| `hyperliquid/api.py` | SDK 客户端封装 |
| `hyperliquid/utils.py` | 时间转换 / 重试工具 |
| `hyperliquid/candles.py` | K 线数据 |
| `hyperliquid/funding.py` | 资金费率 |
| `hyperliquid/oi.py` | 持仓量 |
| `hyperliquid/orderbook.py` | 订单簿 |
| `hyperliquid/cache.py` | SQLite 缓存管理 |
| `hyperliquid/main.py` | 统一数据入口 |
| `tests/test_*.py` | 各模块单元测试 |

---

## 验收标准

- [ ] `get_candles("BTC", "1h", 7)` 返回 7×24=168 条 DataFrame
- [ ] `get_current_funding("BTC")` 返回包含 `funding_rate` 和 `annualized` 的 dict
- [ ] `get_open_interest("BTC")` 返回包含 `open_interest_usd` 的 dict
- [ ] `get_orderbook("BTC")` 返回 bids/asks 列表
- [ ] `get_hl_data("BTC", "2026-03-25")` 返回聚合数据
- [ ] 缓存命中时第二次调用 < 100ms
- [ ] Mock 测试全部通过

---

## 预计工时

| 子任务 | 预计时间 |
|--------|---------|
| T1.2.1 api.py | 1 小时 |
| T1.2.2 utils.py | 1 小时 |
| T1.2.3 candles.py | 2 小时 |
| T1.2.4 funding.py | 1 小时 |
| T1.2.5 oi.py | 1 小时 |
| T1.2.6 orderbook.py | 1 小时 |
| T1.2.7 cache.py | 2 小时 |
| T1.2.8 main.py | 1 小时 |
| T1.2.9 测试 | 3 小时 |
| **合计** | **~13 小时（2 天）** |

---

## 风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| `meta_and_asset_ctxs()` 返回所有币，需要解析 symbol | 性能/格式问题 | 按需过滤 |
| K 线时间窗口计算错误 | 数据不完整 | 写 `calc_time_range` 单元测试 |
| 缓存并发写入 | 数据损坏 | 使用 SQLite WAL 模式 |
