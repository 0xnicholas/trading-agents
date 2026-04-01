# M1.0：SDK 探测验证

**状态**: ✅ 已完成
**完成日期**: 2026-04-01
**负责人**: 已完成（源码克隆自 /tmp/hl-sdk）

---

## 任务目标

验证 Hyperliquid Python SDK 的 Info API 端点，确认各方法的返回数据结构、字段名称、时间戳格式，为后续数据层开发提供准确依据。

---

## 交付物

`docs/sdk_findings.md`

---

## 已验证端点

| 方法 | 用途 | 关键字段 |
|------|------|---------|
| `info.meta_and_asset_ctxs()` | 所有币元数据 + OI + funding | `funding`, `openInterest`, `markPx`, `oraclePx` |
| `info.all_mids()` | 所有币中间价 | `{"BTC": "67000.0", ...}` |
| `info.l2_snapshot(name)` | 订单簿深度 | `levels[0]=bids, levels[1]=asks` |
| `info.candles_snapshot(name, interval, startTime, endTime)` | K 线 | `T(ms), c, h, l, o, v, n(成交笔数)` |
| `info.funding_history(name, startTime, endTime)` | 历史资金费率 | `coin, fundingRate, premium, time` |

---

## 关键发现

1. **时间戳**：K 线 `candles_snapshot` 用毫秒，`l2_snapshot` 用毫秒，返回数据中 `time` 字段 K 线是秒、订单簿是毫秒
2. **symbol 格式**：永续代币名称如 `"BTC"`, `"ETH"`，**不需要** `-PERP` 后缀
3. **全能接口**：`meta_and_asset_ctxs()` 单次调用获取全市场数据，效率最高
4. **无当前 OI 端点**：OI 必须从 `meta_and_asset_ctxs()` 或 `activeAssetCtx` websocket 获取
5. **无当前资金费率端点**：必须用 `funding_history()` 取最近一条记录

---

## 后续影响

- 数据层直接复用以上端点和字段名
- 不需要额外探索其他端点
