# Hyperliquid SDK 验证结果

**验证时间**: 2026-04-01
**源码**: https://github.com/hyperliquid-dex/hyperliquid-python-sdk (克隆于 /tmp/hl-sdk)

---

## Info API 端点清单（已验证）

### 市场数据端点

| 方法 | 用途 | 返回 |
|------|------|------|
| `info.all_mids()` | 所有币种当前中间价 | `{"BTC": "67000.0", "ETH": "3500.0", ...}` |
| `info.meta()` | 交易对元数据 | `{"universe": [{"name": "BTC", "szDecimals": 5}, ...]}` |
| `info.meta_and_asset_ctxs()` | **全能接口**：元数据 + 资产上下文 | `[{universe: [...]}, [{funding, openInterest, markPx, oraclePx, ...}, ...]]` |
| `info.l2_snapshot(name)` | 订单簿深度 | `{coin, levels: [bids, asks], time}` |
| `info.candles_snapshot(name, interval, startTime, endTime)` | K 线 | `[{"T": t, "c": "67000", "h": ..., "l": ..., "o": ..., "v": ..., "s": "ok"}, ...]` |
| `info.funding_history(name, startTime, endTime)` | 历史资金费率 | `[{coin, fundingRate, premium, time}, ...]` |
| `info.user_funding_history(user, startTime, endTime)` | 用户资金历史 | 同上格式 |
| `info.spot_user_state(address)` | 用户现货状态 | ... |
| `info.open_orders(address)` | 用户挂单 | ... |

### WebSocket 订阅（可选，Phase 1 不需要）

- `info.subscribe({"type": "l2Book", "coin": "BTC"})`
- `info.subscribe({"type": "candle", "coin": "BTC", "interval": "1h"})`
- `info.subscribe({"type": "activeAssetCtx", "coin": "BTC"})` — 实时 OI + funding

---

## 关键数据结构

### PerpAssetCtx（`meta_and_asset_ctxs()` 返回的资产上下文）

```python
{
    "funding": "0.0001",        # 当前资金费率（8h 费率，如 0.0001 = 0.01%）
    "openInterest": "500000000",  # 持仓量（USD）
    "prevDayPx": "66000.0",      # 前一日收盘价
    "dayNtlVlm": "1234567",      # 当日名义成交量（USD）
    "premium": "0.00005",        # 溢价
    "oraclePx": "67000.0",       # 预言机价格
    "markPx": "67050.0",         # 标记价格
    "midPx": "67025.0",          # 中间价
    "impactPxs": ["66900.0", "67100.0"],  # 影响价格（多空双方）
    "dayBaseVlm": "1234.5",      # 当日基础成交量（币）
}
```

**重要**: `openInterest` 是**全市场总 OI**，不是单一币种的；需要单位换算（除以 `10^szDecimals` 或直接从 markPx 计算）。

### CandleSnapshot（K 线）

```python
{
    "T": 1684702007000,   # Unix ms
    "c": "67000.0",       # close
    "h": "67200.0",       # high
    "l": "66800.0",       # low
    "o": "66900.0",       # open
    "v": "1234.5",        # volume（币）
    "i": "1h",            # interval
    "n": 123,             # 成交笔数
    "s": "ok",            # status
    "t": 1684702007,      # 交易所时间（Unix 秒）
}
```

### L2Book（订单簿）

```python
{
    "coin": "BTC",
    "levels": [
        [  # bids
            {"n": 1, "px": "66900.0", "sz": "1.5"},   # n=档位序号, px=价格, sz=数量
            {"n": 2, "px": "66800.0", "sz": "2.3"},
            ...
        ],
        [  # asks
            {"n": 1, "px": "67100.0", "sz": "1.2"},
            ...
        ]
    ],
    "time": 1684702007000
}
```

---

## Symbol 命名规则

SDK 内部通过 `name_to_coin` 字典映射币种名称（如 `"BTC"` → asset id）。币种名称格式：

- 永续合约：`"BTC"`, `"ETH"`, `"SOL"`, `"kPEPE"` 等
- **不需要加 "-PERP" 后缀**（SDK 内部处理）

---

## 时间戳说明

- `candles_snapshot`: `startTime` / `endTime` 用 **毫秒** Unix timestamp
- `funding_history`: `startTime` / `endTime` 用 **毫秒** Unix timestamp
- 返回数据中的 `time` 字段：K 线用**秒**，订单簿用**毫秒**

---

## 重要发现

1. **`meta_and_asset_ctxs()` 是 Phase 1 最重要的端点** — 单次调用获取所有币种的 funding / OI / markPx / oraclePx，数据量最小，效率最高。

2. **没有直接的"当前 OI"端点** — 必须从 `meta_and_asset_ctxs()` 获取当前 OI，或用 `activeAssetCtx` websocket 订阅获取实时更新。

3. **没有直接的"当前资金费率"端点** — 必须用 `funding_history(name, startTime, endTime)` 取最近一条记录，或 websocket 订阅 `activeAssetCtx`。

4. **K 线 `candles_snapshot` 需要 `startTime`/`endTime`** — 不能只传"最近 N 条"，必须计算时间窗口。需要自己处理时间计算。

5. **Python 版本**：`hyperliquid-python-sdk` 依赖 `requests`，不依赖 `poetry` 本身。SDK README 说需要 Poetry v2 以下，但这是开发环境要求，不是运行时要求。运行时只需 Python 3.10+。

---

## API 调用效率分析（Phase 1 估算）

单次 `propagate("BTC", "2026-03-25")` 需要的最小 API 调用：

| 数据 | 端点 | 次数 |
|------|------|------|
| 所有币元数据 + OI + funding | `meta_and_asset_ctxs()` | 1 |
| BTC 订单簿 | `l2_snapshot("BTC")` | 1 |
| BTC K 线（1h × 168） | `candles_snapshot("BTC", "1h", start, end)` | 1 |
| BTC K 线（4h × 42） | `candles_snapshot("BTC", "4h", start, end)` | 1 |
| BTC K 线（1d × 7） | `candles_snapshot("BTC", "1d", start, end)` | 1 |
| **合计** | | **5 次** |

加上容错重试，预计 ≤ 10 次 HTTP 调用，远低于原计划 20 次上限。
