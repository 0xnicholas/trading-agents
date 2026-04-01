# Phase 2：ETH / Solana 多链扩展

**周期**: 2-3 周
**前置条件**: Phase 1 完成并通过验收
**目标**: 在 Hyperliquid 单链基础上，新增 Ethereum 和 Solana 数据层及对应 Analyst，形成跨链分析能力

**已确认设计决策**：
- Solana = 现货 DEX 分析（重点：Memecoin 流动性）
- BTC.D / Fear & Greed / Stablecoin Flow = 接受近似值 + 置信度标注

---

## 里程碑

### M2.0：数据源探测验证（Day 1-2，与 M1.x 并行）

- [ ] CoinGecko `/global` 端点 → 验证 BTC.Dominance 返回格式
- [ ] Alternative.me Fear & Greed API → 验证返回格式
- [ ] Dune Analytics 公共查询 → Stablecoin Flow 查询验证
- [ ] Binance Futures `/fapi/v1/fundingRate` → ETH-PERP 费率验证
- [ ] Jupiter API → Solana 价格/DEX 数据验证
- [ ] GeckoTerminal → Solana Meme 币热度验证
- [ ] 输出：`docs/phase2_data_sources.md`

### M2.1：数据层扩展 — Ethereum（Day 3-7）

#### 价格/现货数据
- [ ] `dataflows/ethereum/price.py` — CoinGecko 获取 ETH 现货 OHLCV
  - 主要用途：**现货价格参考**，用于与 Hyperliquid ETH-PERP 标记价格对比
  - 验证标记价格偏差 > 1% 时发出警告

#### 永续合约资金费率
- [ ] `dataflows/ethereum/funding.py` — Binance Futures API
  - 端点：`GET /fapi/v1/fundingRate?symbol=ETHUSDT`
  - 每 8 小时更新，与 Hyperliquid 资金费率**分开展示**
  - 年化计算：`(rate × 3 × 365)`

#### 链上数据
- [ ] `dataflows/ethereum/onchain.py` — Alchemy RPC 或 Dune API
  - **活跃地址数**：Dune 公共查询（`ethereum.addresses.active`）
  - **Gas 价格**：Etherscan Gas API（免费，`/gastracker`）
  - **ETH 质押量**：从链上 Staking 合约计算或 CoinGecko
  - **TVL**：DeFiLlama API（免费，无 Key）

#### ETH 数据汇总
- [ ] `ethereum.py` — 主入口，统一输出格式

### M2.2：数据层扩展 — Solana（Day 8-14）

#### 现货价格
- [ ] `dataflows/solana/price.py` — Jupiter Price API
  - 端点：`GET /price?ids=SOL&vsToken=USDT`
  - 现货价格作为 Solana DEX 分析的基准

#### DEX 流动性
- [ ] `dataflows/solana/dex.py` — Jupiter + Raydium Subgraph（The Graph）
  - Jupiter API：DEX 价格聚合
  - Raydium Subgraph：流动性池状态（TVL / 24h 成交量）
  - 重点币种：MEME 币（`$DOGE`, `$WIF`, `$BOME`, `$SLERF` 等）

#### Meme 币热度
- [ ] `dataflows/solana/meme.py` — GeckoTerminal API
  - 端点：GeckoTerminal Solana DEX 聚合数据
  - 数据：流动性 / 24h 成交量 / 买卖压力
  - 支持 Top Meme 币榜单

#### Solana 数据汇总
- [ ] `solana.py` — 主入口，统一输出格式

### M2.3：ETH OnChain Analyst（Day 10-12）
- [ ] `agents/analysts/ethereum_onchain_analyst.py`
  - **Gas 情绪**：当前 Gas vs 7d 均值（高 Gas = 链上活跃 = 市场热度高）
  - **活跃地址趋势**：30 天活跃地址变化率
  - **质押率**：ETH Staking 比例（高质押率 = 看涨持有倾向）
  - **DeFi TVL**：ETH DeFi TVL vs 全市场占比
  - **资金费率对比**：Binance ETH-PERP vs Hyperliquid ETH-PERP 资金费率差异

**Prompt 方向**：
```
你是一个 Ethereum 链上数据分析师。
给定：Gas价格 / 活跃地址 / Staking 比例 / TVL / 现货价格
输出 JSON（标注置信度）：
{
    "summary": "ETH 链上状态...",
    "confidence": 0.85,  // 数据完整度
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

### M2.4：Solana DEX / Meme Analyst（Day 10-12）
- [ ] `agents/analysts/solana_dex_analyst.py`
  - **Meme 币流动性**：Top Meme 币的流动性深度
  - **Meme 币资金流向**：24h 成交量 vs 流动性比率（高周转率 = 投机热度高）
  - **SOL 价格动能**：SOL 现货 24h 价格变化
  - **DEX 活动度**：Raydium / Jupiter 成交量变化

**Prompt 方向**：
```
你是一个 Solana DEX 和 Meme 币数据分析师。
给定：SOL 价格 / DEX 流动性 / Meme 币热度数据
输出 JSON：
{
    "summary": "Solana Meme 市场状态...",
    "confidence": 0.75,  // Solana RPC 数据不稳定，置信度较低
    "signals": {
        "meme_liquidity": {"value": "adequate", "confidence": 0.8},
        "meme_turnover": {"value": 2.5, "label": "elevated_speculation"},
        "sol_momentum": {"value": 0.05, "label": "bullish_24h"},
        "dex_volume_rank": {"value": 2, "label": "top2_dex"}
    },
    "narrative": "..."
}
```

### M2.5：跨链 Macro Analyst（Day 13-16）

#### M2.5.1 BTC.Dominance
- [ ] 数据源：CoinGecko `/global`（免费）
- [ ] 计算：BTC 市值 / 加密总市值 × 100
- [ ] 周期：每日快照，计算 7d 趋势

#### M2.5.2 Fear & Greed Index
- [ ] 数据源：Alternative.me API（免费）
- [ ] 周期：每日快照
- [ ] 标注：**免费数据置信度低**，作为辅助参考

#### M2.5.3 Stablecoin Flow（近似方案）
- [ ] 近似指标 1：Etherscan USDT 转账量（作为链上稳定币活跃度代理）
- [ ] 近似指标 2：CoinGecko 稳定币市值总供给变化
- [ ] **不追求高精度**：标注"近似值，置信度 0.5"

#### M2.5.4 Cross-Chain 相关性
- [ ] 计算：7d 收盘价 Pearson 相关系数（BTC vs ETH, BTC vs SOL）
- [ ] 数据源：CoinGecko 每日收盘价
- [ ] 高相关（>0.8）= 市场同向；低相关（<0.5）= 板块分化

**输出 Schema**：
```json
{
    "summary": "跨链宏观：短期偏谨慎，风险偏好下降",
    "confidence": 0.65,
    "market_regime": "risk_off",
    "btc_dominance": {
        "value": 52.3,
        "trend": "rising",
        "verdict": "资金轮动到 BTC",
        "confidence": 0.85
    },
    "fear_greed": {
        "value": 35,
        "label": "恐惧",
        "confidence": 0.5
    },
    "stablecoin_flow": {
        "usdt_supply_change_24h": 500000000,
        "verdict": "流入增加，多头信号",
        "confidence": 0.5
    },
    "cross_chain_correlation": {
        "btc_eth_corr_7d": 0.85,
        "btc_sol_corr_7d": 0.72,
        "verdict": "高相关性，市场同向",
        "confidence": 0.8
    },
    "narrative": "..."
}
```

### M2.6：Graph 升级 — 多链路由（Day 17-19）
- [ ] `graph/crypto_trading_graph.py` 改造
  - `propagate(symbol, date, chains=["hyperliquid", "ethereum", "solana"])`
  - Chain-Specific Analyst **并行执行**（async）
  - Cross-Chain Macro Analyst 在所有链数据就绪后执行
- [ ] `agents/trader/crypto_trader.py` 改造
  - 汇总三链 Analyst 报告
  - 输出综合方向判断（多链一致 vs 分歧）
- [ ] 配置升级
  ```python
  "chains": {
      "hyperliquid": {"enabled": True, "data": ["perp", "orderbook", "funding"]},
      "ethereum": {"enabled": True, "data": ["onchain", "spot_price", "funding"]},
      "solana": {"enabled": True, "data": ["dex", "meme", "spot_price"]},
  }
  ```

### M2.7：集成测试（Day 20-21）
- [ ] 多链并行分析（BTC-PERP / ETH / SOL）
- [ ] Cross-Chain Macro Analyst 输出（含置信度标注）
- [ ] 单链数据失败时的降级测试
- [ ] 性能基准（多链响应时间）

---

## 数据源详情（已验证/规划）

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
| Stablecoin Flow | Etherscan USDT 转账量代理 | 免费 | 0.5 |
| 相关性 | CoinGecko 收盘价计算 | 限速 | 0.8 |

---

## 置信度标注规范

所有来自免费/不稳定数据源的数据，输出必须包含 `confidence` 字段：

| 数据质量 | confidence | 说明 |
|---------|-----------|------|
| 官方 API / SDK | 0.9-1.0 | Hyperliquid SDK, Binance API |
| 付费 API（稳定） | 0.8-0.9 | Dune 有 Key, Alchemy |
| 免费 API（限速） | 0.7-0.8 | CoinGecko, Jupiter |
| 近似/代理指标 | 0.4-0.6 | USDT 转账量代理 |
| 低质量/估算 | 0.3-0.5 | Fear & Greed 免费版 |

---

## 验收标准

### 功能验收

| 功能 | 验收条件 |
|------|---------|
| ETH 现货价格 | CoinGecko 返回 vs Hyperliquid markPx 偏差 < 1% |
| Binance ETH-PERP 资金费率 | 每 8h 费率获取成功 |
| Solana SOL 价格 | Jupiter 返回正确价格 |
| Solana DEX Meme 流动性 | Top 5 Meme 币流动性数据获取 |
| BTC.Dominance | 7d 趋势计算正确 |
| Fear & Greed | 每日值获取 + 标注置信度 |
| Stablecoin Flow 近似 | Etherscan USDT 转账量代理指标计算 |
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

## 修订说明

| # | 问题 | 修订 |
|---|------|------|
| 1 | BTC.D 无数据源 | ✅ CoinGecko `/global` |
| 2 | Fear & Greed 无源 | ✅ Alternative.me，置信度 0.5 |
| 3 | Stablecoin Flow 未定义 | ✅ USDT Etherscan 转账量代理，置信度 0.5 |
| 4 | ETH 费率来源冲突 | ✅ 统一 Binance Futures，Hyperliquid 分开展示 |
| 5 | Solana 永续不需要 | ✅ 明确为现货 DEX 分析 |
| 6 | DEX API 可靠性 | ✅ Jupiter 为主，Raydium Subgraph 补充 |
| 7 | Dune 免费层不足 | ✅ 改用 DeFiLlama（免费无 Key）+ Etherscan |
| 8 | M2.3/M2.4 时间重叠 | ✅ 改为串行（先 ETH 再 SOL） |
| 9 | 相关性计算未定义 | ✅ 7d Pearson，数据源 CoinGecko |
| 10 | ETH 数据混淆 | ✅ 区分：现货参考 + PERP 费率（Hyperliquid）|
| 11 | 配置层太简单 | ✅ 嵌套 chains 配置 |
| 12 | 数据降级策略模糊 | ✅ 分 core/optional + 置信度标注 |

---

*Phase 2 完成后，项目具备完整的跨链多 Agent 分析能力。Phase 3 重点构建风控和回测。*
