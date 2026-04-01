# Phase 2：ETH / Solana 多链扩展

**状态**: 🔵 待启动
**周期**: 2-3 周
**前置条件**: Phase 1 完成 ✅

---

## 目标

在 Hyperliquid 单链基础上，新增 Ethereum 和 Solana 数据层及对应 Analyst，形成跨链分析能力。

**核心设计决策**：
- Solana = 现货 DEX 分析（重点：Memecoin 流动性）
- BTC.D / Fear & Greed / Stablecoin Flow = 接受近似值 + 置信度标注

---

## 里程碑总览

| 里程碑 | 名称 | 周期 | 状态 |
|--------|------|------|------|
| M2.0 | 数据源探测验证 | Day 1-2 | 🔵 待启动 |
| M2.1 | 数据层扩展 — Ethereum | Day 3-6 | ⏸️ 等待中 |
| M2.2 | 数据层扩展 — Solana | Day 4-10 | ⏸️ 等待中 |
| M2.3 | ETH OnChain Analyst | Day 3-6 | ⏸️ 等待中 |
| M2.4 | Solana DEX / Meme Analyst | Day 7-10 | ⏸️ 等待中 |
| M2.5 | 跨链 Macro Analyst | Day 11-14 | ⏸️ 等待中 |
| M2.6 | Graph 升级 — 多链路由 | Day 15-18 | ⏸️ 等待中 |
| M2.7 | 集成测试 | Day 19-21 | ⏸️ 等待中 |

---

## 详细任务分解

### M2.0 数据源探测验证（Day 1-2）

**预计工时**: 10h
**前置**: 无

| 任务 | 子任务 | 数据源 | 验证内容 | 状态 |
|------|--------|--------|---------|------|
| T2.0.1 | CoinGecko `/global` 端点验证 | CoinGecko API | BTC.Dominance 返回格式 | 🔵 |
| T2.0.2 | Alternative.me Fear & Greed 验证 | Alternative.me API | 返回格式、值范围 0-100 | 🔵 |
| T2.0.3 | Binance Futures fundingRate 验证 | Binance API | ETHUSDT fundingRate 格式 | 🔵 |
| T2.0.4 | Jupiter API 价格验证 | Jupiter | SOL/USDT 价格格式 | 🔵 |
| T2.0.5 | GeckoTerminal Solana Meme 验证 | GeckoTerminal | DEX 聚合数据格式 | 🔵 |
| T2.0.6 | DeFiLlama TVL API 验证 | DeFiLlama | ETH/SOL TVL 格式 | 🔵 |
| T2.0.7 | 输出数据源文档 | — | `docs/phase2_data_sources.md` | 🔵 |
| T2.0.8 | CoinGecko 限流测试 | — | 验证 30 calls/min 内不触发 429 | 🔵 |

**交付物**: `docs/phase2_data_sources.md`

---

### M2.1 数据层扩展 — Ethereum（Day 3-6）

**预计工时**: 12h
**并行**: 与 M2.3 ETH Analyst 并行开发

#### M2.1.1 包结构

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.1.0 | `dataflows/ethereum/__init__.py` | 🔵 |

#### M2.1.2 价格数据

| 任务 | 子任务 | 数据源 | 状态 |
|------|--------|--------|------|
| T2.1.1 | `dataflows/ethereum/price.py` — CoinGecko ETH 现货 OHLCV | CoinGecko | 🔵 |
| T2.1.2 | `check_price_deviation(eth_price, hl_mark_px)` — 偏差 > 1% 返回警告 + confidence -0.1 | — | 🔵 |

#### M2.1.3 永续合约资金费率

| 任务 | 子任务 | 数据源 | 状态 |
|------|--------|--------|------|
| T2.1.3 | `dataflows/ethereum/funding.py` — Binance Futures API | Binance | 🔵 |
| T2.1.4 | 年化计算 (`rate × 3 × 365`) | — | 🔵 |
| T2.1.5 | 与 Hyperliquid 资金费率分开展示 | — | 🔵 |

#### M2.1.4 链上数据

| 任务 | 子任务 | 数据源 | 优先级 | 状态 |
|------|--------|--------|--------|------|
| T2.1.6 | `dataflows/ethereum/onchain.py` — Gas 价格 | Etherscan Gas API | 高 | 🔵 |
| T2.1.7 | ETH 质押量 — `get_staking_ratio()` | CoinGecko | 高 | 🔵 |
| T2.1.8 | DeFi TVL — `get_defi_tvl()` | DeFiLlama API | 高 | 🔵 |
| T2.1.9 | 活跃地址数（可选）— `get_active_addresses()` | CoinGecko on-chain | 低 | 🔵 |

#### M2.1.5 ETH 数据汇总

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.1.10 | `dataflows/ethereum/main.py` — 统一入口 | 🔵 |
| T2.1.11 | ETH 数据层测试 | 🔵 |

---

### M2.2 数据层扩展 — Solana（Day 4-10）

**预计工时**: 16h
**并行**: 与 M2.4 Solana Analyst 并行开发

#### M2.2.1 包结构

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.2.0 | `dataflows/solana/__init__.py` | 🔵 |

#### M2.2.2 现货价格

| 任务 | 子任务 | 数据源 | 状态 |
|------|--------|--------|------|
| T2.2.1 | `dataflows/solana/price.py` — Jupiter Price API | Jupiter | 🔵 |

#### M2.2.3 DEX 流动性

| 任务 | 子任务 | 数据源 | 状态 |
|------|--------|--------|------|
| T2.2.2 | `dataflows/solana/dex.py` — Jupiter DEX 聚合 | Jupiter API | 🔵 |
| T2.2.3 | Raydium Subgraph — 流动性池状态（备选）| The Graph | 🔵 |

#### M2.2.4 Meme 币热度

| 任务 | 子任务 | 数据源 | 状态 |
|------|--------|--------|------|
| T2.2.4 | `dataflows/solana/meme.py` — GeckoTerminal API | GeckoTerminal | 🔵 |
| T2.2.5 | Top Meme 币榜单支持 | — | 🔵 |

#### M2.2.5 Solana 数据汇总

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.2.6 | `dataflows/solana/main.py` — 统一入口 | 🔵 |
| T2.2.7 | Solana 数据层测试 | 🔵 |

---

### M2.3 ETH OnChain Analyst（Day 3-6）

**预计工时**: 12h
**并行**: 与 M2.1 ETH 数据层并行

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.3.1 | `agents/analysts/ethereum_onchain_analyst.py` — 主体 | 🔵 |
| T2.3.2 | Gas 情绪分析 (vs 7d 均值) | 🔵 |
| T2.3.3 | `active_address_trend` signal — 30d 变化率 > 10% = rising, < -10% = falling | 🔵 |
| T2.3.4 | ETH 质押率分析 | 🔵 |
| T2.3.5 | DeFi TVL 分析 | 🔵 |
| T2.3.6 | 资金费率对比 (Binance vs Hyperliquid) | 🔵 |
| T2.3.7 | Pydantic Schema `EthereumOnChainReport` — 字段: summary, direction, confidence, signals{gas_sentiment, active_address_trend, staking_ratio, tvl_rank, funding_diff}, narrative | 🔵 |
| T2.3.8 | ETH Analyst 测试 | 🔵 |

**输出 Schema**:
```json
{
  "summary": "ETH 链上状态...",
  "confidence": 0.85,
  "signals": {
    "gas_sentiment": {"value": "high", "confidence": 0.9},
    "active_address_trend": {"value": "rising", "confidence": 0.7},
    "staking_ratio": {"value": 0.28, "label": "elevated"},
    "tvl_rank": {"value": 0.65, "label": "dominant"},
    "funding_diff": {"value": 0.0001, "note": "Binance vs HL diff"}
  },
  "narrative": "..."
}
```

---

### M2.4 Solana DEX / Meme Analyst（Day 7-10）

**预计工时**: 12h

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.4.1 | `agents/analysts/solana_dex_analyst.py` — 主体 | 🔵 |
| T2.4.2 | Meme 币流动性分析 | 🔵 |
| T2.4.3 | Meme 币资金流向 (24h周转率) | 🔵 |
| T2.4.4 | SOL 价格动能 | 🔵 |
| T2.4.5 | DEX 活动度 (Raydium/Jupiter) | 🔵 |
| T2.4.6 | Pydantic Schema `SolanaDexReport` — 字段: summary, direction, confidence, signals{meme_liquidity, meme_turnover, sol_momentum, dex_volume_rank}, narrative | 🔵 |
| T2.4.7 | Solana Analyst 测试 | 🔵 |

**输出 Schema**:
```json
{
  "summary": "Solana Meme 市场状态...",
  "confidence": 0.75,
  "signals": {
    "meme_liquidity": {"value": "adequate", "confidence": 0.8},
    "meme_turnover": {"value": 2.5, "label": "elevated_speculation"},
    "sol_momentum": {"value": 0.05, "label": "bullish_24h"},
    "dex_volume_rank": {"value": 2, "label": "top2_dex"}
  },
  "narrative": "..."
}
```

---

### M2.5 跨链 Macro Analyst（Day 11-14）

**预计工时**: 16h

#### M2.5.1 包结构

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.5.0 | `dataflows/macro/__init__.py` | 🔵 |

#### M2.5.2 BTC Dominance

| 任务 | 子任务 | 数据源 | 状态 |
|------|--------|--------|------|
| T2.5.1 | BTC.D 计算 | CoinGecko `/global` | 🔵 |
| T2.5.2 | 7d 趋势计算 | — | 🔵 |

#### M2.5.3 Fear & Greed Index

| 任务 | 子任务 | 数据源 | 置信度 | 状态 |
|------|--------|--------|--------|------|
| T2.5.3 | Fear & Greed 获取 | Alternative.me | 0.5 | 🔵 |

#### M2.5.4 Stablecoin Flow（近似方案）

| 任务 | 子任务 | 数据源 | 置信度 | 状态 |
|------|--------|--------|--------|------|
| T2.5.4 | USDT 转账量代理指标 | Etherscan | 0.5 | 🔵 |
| T2.5.5 | 稳定币市值供给变化 | CoinGecko | 0.5 | 🔵 |

#### M2.5.5 Cross-Chain 相关性

| 任务 | 子任务 | 数据源 | 状态 |
|------|--------|--------|------|
| T2.5.6 | 获取 BTC 7d 每日收盘价 | CoinGecko | 🔵 |
| T2.5.7 | 获取 ETH 7d 每日收盘价 | CoinGecko | 🔵 |
| T2.5.8 | 获取 SOL 7d 每日收盘价 | CoinGecko | 🔵 |
| T2.5.9 | 7d Pearson 相关系数计算 | — | 🔵 |
| T2.5.10 | BTC vs ETH, BTC vs SOL 相关性分析 | — | 🔵 |

#### M2.5.6 Macro Analyst 主体

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.5.11 | `agents/analysts/cross_chain_macro_analyst.py` | 🔵 |
| T2.5.12 | Pydantic Schema `CrossChainMacroReport` | 🔵 |
| T2.5.13 | Macro Analyst 测试 | 🔵 |

#### M2.5.7 Macro 数据汇总

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.5.14 | `dataflows/macro/main.py` — 宏观数据统一入口 | 🔵 |
| T2.5.15 | `get_macro_data()` — 并行获取 BTC.D / Fear&Greed / StablecoinFlow / Correlation | 🔵 |

**输出 Schema**:
```json
{
  "summary": "跨链宏观：短期偏谨慎，风险偏好下降",
  "confidence": 0.65,
  "market_regime": "risk_off",
  "btc_dominance": {"value": 52.3, "trend": "rising", "verdict": "...", "confidence": 0.85},
  "fear_greed": {"value": 35, "label": "恐惧", "confidence": 0.5},
  "stablecoin_flow": {"usdt_supply_change_24h": 500000000, "verdict": "...", "confidence": 0.5},
  "cross_chain_correlation": {"btc_eth_corr_7d": 0.85, "btc_sol_corr_7d": 0.72, "confidence": 0.8},
  "narrative": "..."
}
```

---

### M2.6 Graph 升级 — 多链路由（Day 15-18）

**预计工时**: 14h

#### M2.6.1 Graph 核心改造

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.6.1 | `graph/crypto_trading_graph.py` 改造 — 状态增加 chains 字段 | 🔵 |
| T2.6.2 | `run_parallel_chains()` — `asyncio.gather` 并行执行多链 Analyst | 🔵 |
| T2.6.3 | `return_exceptions=True` — 单链错误不影响其他链 | 🔵 |
| T2.6.4 | Cross-Chain Macro Analyst 顺序执行（在所有链数据就绪后）| 🔵 |

#### M2.6.2 Trader 多链汇总

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.6.5 | `decide_multi_chain()` — 综合多链报告做出交易决策 | 🔵 |
| T2.6.6 | `create_trader_node` 更新支持多链输入 | 🔵 |

#### M2.6.3 错误处理和降级

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.6.7 | `get_chain_data_with_fallback()` — 单链失败降级，返回 degraded 状态 | 🔵 |
| T2.6.8 | 置信度下调规则实现: 超时 -0.1, 限流 -0.15, 解析失败 -0.2 | 🔵 |

#### M2.6.4 配置

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.6.9 | 多链配置升级 (`ChainsConfig` with `enabled`, `data_types`, `timeout_seconds`) | 🔵 |
| T2.6.10 | Graph 升级测试 | 🔵 |

---

### M2.7 集成测试（Day 19-21）

**预计工时**: 8h

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.7.1 | 多链并行分析 (BTC-PERP / ETH / SOL) | 🔵 |
| T2.7.2 | Cross-Chain Macro Analyst 输出 | 🔵 |
| T2.7.3 | 单链数据失败降级测试 | 🔵 |
| T2.7.4 | 性能基准 (多链响应时间) | 🔵 |
| T2.7.5 | 人工评审 | 🔵 |
| T2.7.6 | 测试报告 | 🔵 |

---

## 置信度标注规范

| 数据质量 | confidence | 来源 |
|---------|-----------|------|
| 官方 API / SDK | 0.9-1.0 | Hyperliquid SDK, Binance API |
| 免费 API（限速但稳定） | 0.7-0.8 | CoinGecko, Jupiter, DeFiLlama |
| 近似/代理指标 | 0.4-0.6 | Etherscan USDT 转账代理 |
| 低质量/估算 | 0.3-0.5 | Fear & Greed 免费版 |

---

## 置信度下调规则

| 错误类型 | 下调幅度 |
|---------|---------|
| API 超时 | -0.1 |
| API 限流 (429) | -0.15 |
| 数据解析失败 | -0.2 |
| 完全不可用 | -0.3 |

---

## API 限流处理

| API | 限制 | 处理策略 |
|-----|------|---------|
| CoinGecko | 10-30 calls/min | 共享缓存，TTL=60s |
| Jupiter | 充足 | 并发请求 |
| Binance | 1200/min | 共享 client |
| Etherscan | 5/sec | 串行 + 缓存 |
| DeFiLlama | 充足 | 直接调用 |

---

## 验收标准

### 功能验收

| 功能 | 验收条件 |
|------|---------|
| ETH 现货价格 | CoinGecko vs Hyperliquid markPx 偏差 < 1% |
| Binance ETH-PERP 资金费率 | 每 8h 费率获取成功 |
| Solana SOL 价格 | Jupiter 返回正确价格 |
| Solana DEX Meme 流动性 | Top 5 Meme 币流动性数据获取 |
| BTC.Dominance | 7d 趋势计算正确 |
| Fear & Greed | 每日值获取 + 标注置信度 0.5 |
| Stablecoin Flow 近似 | Etherscan USDT 转账代理计算 |
| 相关性计算 | BTC/ETH/SOL 7d Pearson 相关系数 |
| ETH OnChain Analyst | 输出含置信度的 JSON |
| SOL DEX Analyst | 输出含置信度的 JSON |
| Cross-Chain Analyst | 输出宏观 regime 判断 |
| 多链汇聚 | Trader Agent 汇总正确 |

### 非功能验收

| 维度 | 验收条件 |
|------|---------|
| 多链 API 调用 | 单次 ≤ 40 次 HTTP |
| 响应时间 | 多链 < 60s |
| 数据降级 | 单链失败不影响其他链 |
| 置信度标注 | 所有近似数据都有 confidence 字段 |

---

## 数据源汇总

### Ethereum

| 数据 | 来源 | 免费额度 | 用途 | 置信度 |
|------|------|---------|------|--------|
| ETH 现货价格 | CoinGecko | 限速 | 现货基准 | 0.75 |
| ETH-PERP 资金费率 | Binance Futures API | 免费 | CEX 费率基准 | 0.9 |
| Gas 价格 | Etherscan Gas API | 5/sec | 链上热度 | 0.8 |
| 活跃地址（可选）| CoinGecko on-chain | 限速 | 链上活跃度 | 0.5 |
| ETH Staking | CoinGecko | 免费 | 持有倾向 | 0.75 |
| DeFi TVL | DeFiLlama API | 充足 | 生态健康度 | 0.8 |

### Solana

| 数据 | 来源 | 免费额度 | 用途 | 置信度 |
|------|------|---------|------|--------|
| SOL 价格 | Jupiter Price API | 充足 | 现货基准 | 0.85 |
| DEX 流动性 | Jupiter + Raydium | 充足 | Meme 币流动性 | 0.8 |
| Meme 热度 | GeckoTerminal | 基本免费 | 投机热度 | 0.7 |
| DEX 成交量 | Raydium Subgraph | 有限 | 市场活跃度 | 0.7 |

### 跨链宏观

| 数据 | 来源 | 免费额度 | 置信度 |
|------|------|---------|-------|
| BTC.Dominance | CoinGecko `/global` | 限速 | 0.85 |
| Fear & Greed | Alternative.me | 免费 | 0.5 |
| Stablecoin Flow | Etherscan USDT 转账 | 5/sec | 0.5 |
| 相关性计算 | CoinGecko 收盘价 | 限速 | 0.8 |

---

## 工时汇总

| 里程碑 | 工时 | 累计 |
|--------|------|------|
| M2.0 | 10h | 10h |
| M2.1 | 12h | 22h |
| M2.2 | 16h | 38h |
| M2.3 | 12h | 50h |
| M2.4 | 12h | 62h |
| M2.5 | 16h | 78h |
| M2.6 | 14h | 92h |
| M2.7 | 8h | 100h |

**Phase 2 总工时**: ~100 小时（约 14 个工作日）

---

## 修订记录

| 日期 | # | 问题 | 修订 |
|------|---|------|------|
| 2026-04-01 | 1 | Dune Analytics 自相矛盾 | 删除，新增 DeFiLlama |
| 2026-04-01 | 2 | 活跃地址数据源不明 | 改用 CoinGecko，标为可选 |
| 2026-04-01 | 3 | 相关性计算缺数据获取 | 拆分为 T2.5.6-2.5.10 |
| 2026-04-01 | 4 | M2.3/M2.4/M2.5 时间重叠 | 改为并行 |
| 2026-04-01 | 5 | API 限流未考虑 | 添加限流处理表 |
| 2026-04-01 | 6 | Raydium Subgraph 不稳定 | 标注为备选 |
| 2026-04-01 | 7 | 总工时偏多 | 104h → 96h |
| 2026-04-01 | 8 | 缺少 macro 模块包结构 | 新增 T2.5.0, T2.5.14-15 |
| 2026-04-01 | 9 | 缺少 decide_multi_chain | 新增 T2.6.5-2.6.6 |
| 2026-04-01 | 10 | 缺少置信度降级任务 | 新增 T2.6.7-2.6.8 |
| 2026-04-01 | 11 | 缺少 async 并行任务 | 新增 T2.6.2-2.6.3 |
| 2026-04-01 | 12 | 缺少 check_price_deviation 函数 | T2.1.2 明确为独立函数 |
| 2026-04-01 | 13 | Schema 字段不明确 | T2.3.7, T2.4.6 明确字段列表 |
| 2026-04-01 | 14 | 缺少 __init__.py 任务 | T2.1.0, T2.2.0, T2.5.0 |

---

*Phase 2 完成后，项目具备完整的跨链多 Agent 分析能力。Phase 3 重点构建风控和回测。*
