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
| M2.1 | 数据层扩展 — Ethereum | Day 3-7 | ⏸️ 等待中 |
| M2.2 | 数据层扩展 — Solana | Day 8-14 | ⏸️ 等待中 |
| M2.3 | ETH OnChain Analyst | Day 10-12 | ⏸️ 等待中 |
| M2.4 | Solana DEX / Meme Analyst | Day 13-16 | ⏸️ 等待中 |
| M2.5 | 跨链 Macro Analyst | Day 13-16 | ⏸️ 等待中 |
| M2.6 | Graph 升级 — 多链路由 | Day 17-19 | ⏸️ 等待中 |
| M2.7 | 集成测试 | Day 20-21 | ⏸️ 等待中 |

---

## 详细任务分解

### M2.0 数据源探测验证（Day 1-2）

**预计工时**: 8h
**并行**: 可与 Phase 1 收尾并行

| 任务 | 子任务 | 数据源 | 验证内容 | 状态 |
|------|--------|--------|---------|------|
| T2.0.1 | CoinGecko `/global` 端点验证 | CoinGecko API | BTC.Dominance 返回格式 | 🔵 |
| T2.0.2 | Alternative.me Fear & Greed 验证 | Alternative.me API | 返回格式、值范围 | 🔵 |
| T2.0.3 | Dune Analytics 公共查询验证 | Dune | Stablecoin Flow 查询可行性 | 🔵 |
| T2.0.4 | Binance Futures fundingRate 验证 | Binance API | ETHUSDT fundingRate 格式 | 🔵 |
| T2.0.5 | Jupiter API 价格验证 | Jupiter | SOL/USDT 价格格式 | 🔵 |
| T2.0.6 | GeckoTerminal Solana Meme 验证 | GeckoTerminal | DEX 聚合数据格式 | 🔵 |
| T2.0.7 | 输出数据源文档 | — | `docs/phase2_data_sources.md` | 🔵 |

**交付物**: `docs/phase2_data_sources.md`

---

### M2.1 数据层扩展 — Ethereum（Day 3-7）

**预计工时**: 16h

#### M2.1.1 价格数据

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.1.1 | `dataflows/ethereum/price.py` — CoinGecko ETH 现货 OHLCV | 🔵 |
| T2.1.2 | 标记价格偏差检测 (>1% 警告) | ⏸️ |
| T2.1.3 | `dataflows/ethereum/__init__.py` | ⏸️ |

#### M2.1.2 永续合约资金费率

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.1.4 | `dataflows/ethereum/funding.py` — Binance Futures API | 🔵 |
| T2.1.5 | 年化计算 (`rate × 3 × 365`) | ⏸️ |
| T2.1.6 | 与 Hyperliquid 资金费率分开展示 | ⏸️ |

#### M2.1.3 链上数据

| 任务 | 子任务 | 数据源 | 状态 |
|------|--------|--------|------|
| T2.1.7 | 活跃地址数 | Dune 公共查询 | 🔵 |
| T2.1.8 | Gas 价格 | Etherscan Gas API | 🔵 |
| T2.1.9 | ETH 质押量 | CoinGecko | 🔵 |
| T2.1.10 | DeFi TVL | DeFiLlama API | 🔵 |

#### M2.1.4 ETH 数据汇总

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.1.11 | `dataflows/ethereum/main.py` — 统一入口 | 🔵 |
| T2.1.12 | ETH 数据层测试 | 🔵 |

---

### M2.2 数据层扩展 — Solana（Day 8-14）

**预计工时**: 20h

#### M2.2.1 现货价格

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.2.1 | `dataflows/solana/price.py` — Jupiter Price API | 🔵 |

#### M2.2.2 DEX 流动性

| 任务 | 子任务 | 数据源 | 状态 |
|------|--------|--------|------|
| T2.2.2 | `dataflows/solana/dex.py` — Jupiter DEX 聚合 | Jupiter API | 🔵 |
| T2.2.3 | Raydium Subgraph — 流动性池状态 | The Graph | 🔵 |

#### M2.2.3 Meme 币热度

| 任务 | 子任务 | 数据源 | 状态 |
|------|--------|--------|------|
| T2.2.4 | `dataflows/solana/meme.py` — GeckoTerminal API | GeckoTerminal | 🔵 |
| T2.2.5 | Top Meme 币榜单支持 | — | 🔵 |

#### M2.2.4 Solana 数据汇总

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.2.6 | `dataflows/solana/main.py` — 统一入口 | 🔵 |
| T2.2.7 | Solana 数据层测试 | 🔵 |

---

### M2.3 ETH OnChain Analyst（Day 10-12）

**预计工时**: 12h

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.3.1 | `agents/analysts/ethereum_onchain_analyst.py` — 主体 | 🔵 |
| T2.3.2 | Gas 情绪分析 (vs 7d 均值) | ⏸️ |
| T2.3.3 | 活跃地址趋势 (30d 变化率) | ⏸️ |
| T2.3.4 | ETH 质押率分析 | ⏸️ |
| T2.3.5 | DeFi TVL 分析 | ⏸️ |
| T2.3.6 | 资金费率对比 (Binance vs Hyperliquid) | ⏸️ |
| T2.3.7 | Pydantic Schema (`EthereumOnChainReport`) | 🔵 |
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

### M2.4 Solana DEX / Meme Analyst（Day 13-16）

**预计工时**: 12h

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.4.1 | `agents/analysts/solana_dex_analyst.py` — 主体 | 🔵 |
| T2.4.2 | Meme 币流动性分析 | ⏸️ |
| T2.4.3 | Meme 币资金流向 (24h周转率) | ⏸️ |
| T2.4.4 | SOL 价格动能 | ⏸️ |
| T2.4.5 | DEX 活动度 (Raydium/Jupiter) | ⏸️ |
| T2.4.6 | Pydantic Schema (`SolanaDexReport`) | 🔵 |
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

### M2.5 跨链 Macro Analyst（Day 13-16）

**预计工时**: 16h

#### M2.5.1 BTC Dominance

| 任务 | 子任务 | 数据源 | 状态 |
|------|--------|--------|------|
| T2.5.1 | BTC.D 计算 | CoinGecko `/global` | 🔵 |
| T2.5.2 | 7d 趋势计算 | — | 🔵 |

#### M2.5.2 Fear & Greed Index

| 任务 | 子任务 | 数据源 | 置信度 | 状态 |
|------|--------|--------|--------|------|
| T2.5.3 | Fear & Greed 获取 | Alternative.me | 0.5 | 🔵 |

#### M2.5.3 Stablecoin Flow（近似方案）

| 任务 | 子任务 | 数据源 | 置信度 | 状态 |
|------|--------|--------|--------|------|
| T2.5.4 | USDT 转账量代理指标 | Etherscan | 0.5 | 🔵 |
| T2.5.5 | 稳定币市值供给变化 | CoinGecko | 0.5 | 🔵 |

#### M2.5.4 Cross-Chain 相关性

| 任务 | 子任务 | 数据源 | 状态 |
|------|--------|--------|------|
| T2.5.6 | 7d Pearson 相关系数计算 | CoinGecko | 🔵 |
| T2.5.7 | BTC vs ETH, BTC vs SOL 相关性 | — | 🔵 |

#### M2.5.5 Macro Analyst 主体

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.5.8 | `agents/analysts/cross_chain_macro_analyst.py` | 🔵 |
| T2.5.9 | Pydantic Schema (`CrossChainMacroReport`) | 🔵 |
| T2.5.10 | Macro Analyst 测试 | 🔵 |

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

### M2.6 Graph 升级 — 多链路由（Day 17-19）

**预计工时**: 12h

| 任务 | 子任务 | 状态 |
|------|--------|------|
| T2.6.1 | `graph/crypto_trading_graph.py` 改造 — 并行多链 | 🔵 |
| T2.6.2 | Chain-Specific Analyst 并行执行 (async) | 🔵 |
| T2.6.3 | Cross-Chain Macro Analyst 顺序执行 | ⏸️ |
| T2.6.4 | `agents/trader/crypto_trader.py` 改造 — 汇总三链 | 🔵 |
| T2.6.5 | 多链配置升级 (`chains.enabled` ) | 🔵 |
| T2.6.6 | Graph 升级测试 | 🔵 |

---

### M2.7 集成测试（Day 20-21）

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
| 付费 API（稳定） | 0.8-0.9 | Dune 有 Key, Alchemy |
| 免费 API（限速） | 0.7-0.8 | CoinGecko, Jupiter |
| 近似/代理指标 | 0.4-0.6 | USDT Etherscan 转账代理 |
| 低质量/估算 | 0.3-0.5 | Fear & Greed 免费版 |

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
| Fear & Greed | 每日值获取 + 标注置信度 |
| Stablecoin Flow 近似 | Etherscan USDT 转账代理计算 |
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

| 数据 | 来源 | 免费额度 | 用途 |
|------|------|---------|------|
| ETH 现货价格 | CoinGecko | 限速 | 现货基准 |
| ETH-PERP 资金费率 | Binance Futures API | 免费 | CEX 费率基准 |
| Gas 价格 | Etherscan Gas API | 免费 | 链上热度 |
| 活跃地址 | Dune 公共查询 | 有限额 | 链上活跃度 |
| ETH Staking | CoinGecko | 免费 | 持有倾向 |
| DeFi TVL | DeFiLlama API | 免费 | 生态健康度 |

### Solana

| 数据 | 来源 | 免费额度 | 用途 |
|------|------|---------|------|
| SOL 价格 | Jupiter Price API | 充足 | 现货基准 |
| DEX 流动性 | Jupiter + Raydium Subgraph | 充足 | Meme 币流动性 |
| Meme 热度 | GeckoTerminal | 基本免费 | 投机热度 |
| DEX 成交量 | Raydium Subgraph | 充足 | 市场活跃度 |

### 跨链宏观

| 数据 | 来源 | 免费额度 | 置信度 |
|------|------|---------|-------|
| BTC.Dominance | CoinGecko `/global` | 限速 | 0.85 |
| Fear & Greed | Alternative.me | 免费 | 0.5 |
| Stablecoin Flow | Etherscan USDT 转账代理 | 免费 | 0.5 |
| 相关性 | CoinGecko 收盘价计算 | 限速 | 0.8 |

---

## 工时汇总

| 里程碑 | 工时 | 累计 |
|--------|------|------|
| M2.0 | 8h | 8h |
| M2.1 | 16h | 24h |
| M2.2 | 20h | 44h |
| M2.3 | 12h | 56h |
| M2.4 | 12h | 68h |
| M2.5 | 16h | 84h |
| M2.6 | 12h | 96h |
| M2.7 | 8h | 104h |

**Phase 2 总工时**: ~104 小时（约 15 个工作日，符合 2-3 周计划）

---

## 修订记录

| # | 问题 | 修订 |
|---|------|------|
| 1 | BTC.D 无数据源 | ✅ CoinGecko `/global` |
| 2 | Fear & Greed 无源 | ✅ Alternative.me，置信度 0.5 |
| 3 | Stablecoin Flow 未定义 | ✅ USDT Etherscan 转账代理，置信度 0.5 |
| 4 | ETH 费率来源冲突 | ✅ 统一 Binance Futures，Hyperliquid 分开展示 |
| 5 | Solana 永续不需要 | ✅ 明确为现货 DEX 分析 |
| 6 | DEX API 可靠性 | ✅ Jupiter 为主，Raydium Subgraph 补充 |
| 7 | Dune 免费层不足 | ✅ 改用 DeFiLlama + Etherscan |
| 8 | M2.3/M2.4 时间重叠 | ✅ 改为串行（先 ETH 再 SOL） |
| 9 | 相关性计算未定义 | ✅ 7d Pearson，CoinGecko |
| 10 | ETH 数据混淆 | ✅ 区分：现货参考 + PERP 费率 |
| 11 | 配置层太简单 | ✅ 嵌套 chains 配置 |
| 12 | 数据降级策略模糊 | ✅ 分 core/optional + 置信度标注 |

---

*Phase 2 完成后，项目具备完整的跨链多 Agent 分析能力。Phase 3 重点构建风控和回测。*
