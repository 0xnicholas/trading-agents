# Phase 2 Kanban

**Phase 2 总进度**: 0%
**总任务数**: 65

---

## 待启动 (To Do)

### M2.0 数据源探测验证 (6 tasks)
- [ ] T2.0.1 CoinGecko `/global` 端点验证
- [ ] T2.0.2 Alternative.me Fear & Greed 验证
- [ ] T2.0.3 Binance Futures fundingRate 验证
- [ ] T2.0.4 Jupiter API 价格验证
- [ ] T2.0.5 GeckoTerminal Solana Meme 验证
- [ ] T2.0.6 DeFiLlama TVL API 验证
- [ ] T2.0.7 输出数据源文档

### M2.1 数据层扩展 — Ethereum (12 tasks)
- [ ] T2.1.1 `dataflows/ethereum/price.py` — CoinGecko ETH 现货
- [ ] T2.1.2 标记价格偏差检测 (>1% 警告)
- [ ] T2.1.3 `dataflows/ethereum/__init__.py`
- [ ] T2.1.4 `dataflows/ethereum/funding.py` — Binance Futures API
- [ ] T2.1.5 年化计算 (`rate × 3 × 365`)
- [ ] T2.1.6 与 Hyperliquid 资金费率分开展示
- [ ] T2.1.7 Gas 价格 (Etherscan)
- [ ] T2.1.8 ETH 质押量 (CoinGecko)
- [ ] T2.1.9 DeFi TVL (DeFiLlama)
- [ ] T2.1.10 活跃地址数（可选）(CoinGecko)
- [ ] T2.1.11 `dataflows/ethereum/main.py` — 统一入口
- [ ] T2.1.12 ETH 数据层测试

### M2.2 数据层扩展 — Solana (7 tasks)
- [ ] T2.2.1 `dataflows/solana/price.py` — Jupiter Price API
- [ ] T2.2.2 `dataflows/solana/dex.py` — Jupiter DEX 聚合
- [ ] T2.2.3 Raydium Subgraph（备选）
- [ ] T2.2.4 `dataflows/solana/meme.py` — GeckoTerminal API
- [ ] T2.2.5 Top Meme 币榜单支持
- [ ] T2.2.6 `dataflows/solana/main.py` — 统一入口
- [ ] T2.2.7 Solana 数据层测试

### M2.3 ETH OnChain Analyst (8 tasks)
- [ ] T2.3.1 `agents/analysts/ethereum_onchain_analyst.py`
- [ ] T2.3.2 Gas 情绪分析 (vs 7d 均值)
- [ ] T2.3.3 活跃地址趋势（可选）
- [ ] T2.3.4 ETH 质押率分析
- [ ] T2.3.5 DeFi TVL 分析
- [ ] T2.3.6 资金费率对比 (Binance vs Hyperliquid)
- [ ] T2.3.7 Pydantic Schema (`EthereumOnChainReport`)
- [ ] T2.3.8 ETH Analyst 测试

### M2.4 Solana DEX / Meme Analyst (7 tasks)
- [ ] T2.4.1 `agents/analysts/solana_dex_analyst.py`
- [ ] T2.4.2 Meme 币流动性分析
- [ ] T2.4.3 Meme 币资金流向 (24h周转率)
- [ ] T2.4.4 SOL 价格动能
- [ ] T2.4.5 DEX 活动度 (Raydium/Jupiter)
- [ ] T2.4.6 Pydantic Schema (`SolanaDexReport`)
- [ ] T2.4.7 Solana Analyst 测试

### M2.5 跨链 Macro Analyst (13 tasks)
- [ ] T2.5.1 BTC.D 计算 (CoinGecko)
- [ ] T2.5.2 7d 趋势计算
- [ ] T2.5.3 Fear & Greed 获取 (Alternative.me)
- [ ] T2.5.4 USDT 转账量代理指标 (Etherscan)
- [ ] T2.5.5 稳定币市值供给变化 (CoinGecko)
- [ ] T2.5.6 获取 BTC 7d 每日收盘价
- [ ] T2.5.7 获取 ETH 7d 每日收盘价
- [ ] T2.5.8 获取 SOL 7d 每日收盘价
- [ ] T2.5.9 7d Pearson 相关系数计算
- [ ] T2.5.10 BTC vs ETH, SOL 相关性分析
- [ ] T2.5.11 `agents/analysts/cross_chain_macro_analyst.py`
- [ ] T2.5.12 Pydantic Schema (`CrossChainMacroReport`)
- [ ] T2.5.13 Macro Analyst 测试

### M2.6 Graph 升级 (6 tasks)
- [ ] T2.6.1 Graph 多链改造
- [ ] T2.6.2 Chain Analyst 并行执行
- [ ] T2.6.3 Cross-Chain Macro 顺序执行
- [ ] T2.6.4 Trader Agent 多链汇总
- [ ] T2.6.5 多链配置升级
- [ ] T2.6.6 Graph 升级测试

### M2.7 集成测试 (6 tasks)
- [ ] T2.7.1 多链并行分析
- [ ] T2.7.2 Cross-Chain Macro 输出
- [ ] T2.7.3 单链降级测试
- [ ] T2.7.4 性能基准
- [ ] T2.7.5 人工评审
- [ ] T2.7.6 测试报告

---

## 进行中 (In Progress)

*（暂无）*

---

## 已完成 (Done)

*（暂无）*

---

## 里程碑看板

| 里程碑 | 状态 | 任务数 | 完成 | 日期 |
|--------|------|--------|------|------|
| M2.0 数据源验证 | 🔵 待启动 | 7 | 0/7 | Day 1-2 |
| M2.1 ETH 数据层 | ⏸️ 等待中 | 12 | 0/12 | Day 3-6 |
| M2.2 Solana 数据层 | ⏸️ 等待中 | 7 | 0/7 | Day 4-10 |
| M2.3 ETH Analyst | ⏸️ 等待中 | 8 | 0/8 | Day 3-6 |
| M2.4 Solana Analyst | ⏸️ 等待中 | 7 | 0/7 | Day 7-10 |
| M2.5 Macro Analyst | ⏸️ 等待中 | 13 | 0/13 | Day 11-14 |
| M2.6 Graph 升级 | ⏸️ 等待中 | 6 | 0/6 | Day 15-18 |
| M2.7 集成测试 | ⏸️ 等待中 | 6 | 0/6 | Day 19-21 |

**总计**: 65 任务
**预计工时**: ~96 小时
