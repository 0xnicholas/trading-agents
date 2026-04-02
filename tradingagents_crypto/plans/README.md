# 项目开发计划总览

**项目**: tradingagents_crypto
**目标**: 加密货币永续合约多 Agent 分析系统
**模式**: 纯分析信号（不执行交易）
**主时间周期**: `1h`（核心），`4h` / `1d`（辅助参考）

---

## 已确认架构决策

| 决策 | 结论 |
|------|------|
| Solana 定位 | 现货 DEX 分析，重点：Memecoin 流动性（不做永续合约） |
| 宏观数据置信度 | BTC.D / Fear & Greed / Stablecoin Flow 接受近似值 + 置信度标注 |
| 回测架构 | **路径 A**：规则化信号回测（而非 LLM Agent 决策重放） |
| Portfolio Manager | 新增 `crypto_portfolio_manager.py`（不修改原文件） |
| 波动率指标 | HV（历史波动率）为主，IV（隐含波动率）暂不做 |
| 报告格式 | Markdown 优先，PDF 可选 |
| 回测起始日期 | **待 M3.0 验证**（预期 2024-06 起，Hyperliquid 主网上线时间） |

---

## 四阶段路线图

| 阶段 | 周期 | 目标 | 交付物 | 状态 |
|------|------|------|--------|------|
| **Phase 1** | 2-3 周 | Hyperliquid 单链打样 | 数据层 + 单 Agent + Graph 集成 | ✅ 完成 |
| **Phase 2** | 2-3 周 | ETH / Solana 多链扩展 | 链上数据层 + 跨链 Macro Analyst | ⏭️ 跳过 |
| **Phase 3** | 2-3 周 | 风控 + 回测框架 | Risk Manager Agent + 规则回测引擎 | ✅ 完成 |
| **Phase 4** | 4-6 周 | 生产基础设施 | 日志/监控/CI-CD/Agent工厂/并行执行 | ✅ 完成 |

**总工期**: ~8-12 周（Phase 1/3/4 完成，Phase 2 跳过）

---

## 各阶段文件索引

| 文件 | 内容 |
|------|------|
| `phase-1-hyperliquid.md` | Hyperliquid 单链完整开发计划（含 SDK 验证） |
| `phase-2-multi-chain.md` | ETH / Solana 多链扩展计划（含置信度体系） |
| `phase-3-risk-backtest.md` | 风控 + 回测框架计划（规则回测路径 A） |

---

## Phase 1 核心里程碑（已更新）

| M | 内容 | 关键决策 |
|---|------|---------|
| M1.0 | SDK 探测验证 | 已验证：`candles_snapshot`, `l2_snapshot`, `meta_and_asset_ctxs`, `funding_history` |
| M1.1 | 环境搭建 | Python 3.10 独立虚拟环境 |
| M1.2 | 数据层 | `dataflows/hyperliquid/` 子模块，`ta` 库替代 `stockstats` |
| M1.3 | 配置层 | `mode="crypto"` 路由 |
| M1.4 | 技术指标 | ATR / RSI / MACD / Bollinger / 订单簿不平衡度 |
| M1.5 | Agent 层 | `HyperliquidPerpAnalyst` 输出含 signals/metrics/narrative |
| M1.6 | Graph 集成 | 复用原 graph 模块，替换数据层和 Analyst |
| M1.7 | 端到端测试 | API 调用 ≤ 10 次（因 `meta_and_asset_ctxs` 是全能接口） |

---

## Phase 2 核心里程碑（已更新）

| M | 内容 | 关键决策 |
|---|------|---------|
| M2.0 | 数据源验证 | CoinGecko / Alternative.me / Dune / Jupiter / GeckoTerminal |
| M2.1 | ETH 数据层 | Binance Futures 费率 / DeFiLlama TVL / Etherscan Gas |
| M2.2 | Solana 数据层 | Jupiter 价格 / Raydium Subgraph DEX / GeckoTerminal Meme |
| M2.3 | ETH OnChain Analyst | Gas 情绪 / 活跃地址 / Staking / TVL / 费率对比 |
| M2.4 | SOL DEX Analyst | Meme 流动性 / DEX 成交量 / SOL 动能 |
| M2.5 | Cross-Chain Macro | BTC.D / Fear & Greed / Stablecoin Flow 近似 / 相关性 |
| M2.6 | Graph 多链路由 | Chain-Specific Analyst 并行执行 |
| M2.7 | 集成测试 | 多链 < 40 次 HTTP，< 60s |

### 置信度标注体系

| 数据质量 | confidence |
|---------|-----------|
| 官方 API / SDK | 0.9-1.0 |
| 付费 API（稳定） | 0.8-0.9 |
| 免费 API（限速） | 0.7-0.8 |
| 近似/代理指标 | 0.4-0.6 |
| 低质量/估算 | 0.3-0.5 |

---

## Phase 3 核心里程碑（已更新）

| M | 内容 | 关键决策 |
|---|------|---------|
| M3.0 | 数据范围验证 | 验证 HL 上线时间（预期 2024-06） |
| M3.1 | Risk Manager Agent | LiquidationScenator / HVAnalyst / ExposureMonitor / LiquidityChecker |
| M3.2 | 回测引擎 | **路径 A**：规则化信号回测，非 LLM 重放 |
| M3.3 | 回测数据层 | Parquet 缓存扩展 / 资金费率历史 / 数据完整性检查 |
| M3.4 | 回测案例 | Case 1 MA趋势 / Case 2 资金费率 / Case 3 BTC×SOL跨链 |
| M3.5 | 报告系统 | Markdown 优先 / PDF 可选 |

### 规则回测案例

```
Case 1 - MA 趋势跟踪：
  MA50 > MA200 → 做多
  资金费率 > 15% 年化 → 禁止开空

Case 2 - 资金费率均值回归：
  8h 费率 > 0.01% → 做空
  8h 费率 < -0.01% → 做多

Case 3 - BTC-PERP × SOL-DEX 现货跨链：
  BTC-PERP 1h 涨幅 > 2% → 做多 SOL 现货
  SOL DEX 流动性 < $100k → 跳过
```

---

## 技术约束

- **Python**: `3.10`（Hyperliquid SDK 硬性要求）
- **环境**: 独立虚拟环境 `tradingagents-crypto`
- **依赖管理**: Poetry
- **付费 API**: 可用（Dune / Alchemy / CoinGecko Pro 等）

---

## 开发原则

1. **Phase N 完成后再启动 Phase N+1** — 不提前合并未完成的多链逻辑
2. **数据层先行** — 每个 Phase 先验证数据流，再构建 Agent
3. **接口稳定后再扩展** — 数据格式和 Agent 输出 schema 一旦确定不轻易改动
4. **测试覆盖** — 单测通过才能合并到下阶段
5. **置信度透明** — 所有近似数据必须标注 confidence 字段

---

## 评审节点

| 节点 | 触发条件 | 确认人 |
|------|---------|--------|
| Phase 1 数据层评审 | `hyperliquid_utils.py` + `hyperliquid.py` 完成 | 用户 |
| Phase 1 Agent 评审 | `HyperliquidPerpAnalyst` Prompt 调优完成 | 用户 |
| Phase 1 集成评审 | 端到端 `propagate()` 跑通 | 用户 |
| Phase 2 扩展评审 | ETH / SOL 数据层 + Analyst 跑通 | 用户 |
| Phase 3 交付评审 | 回测引擎 + 风控模块完成 | 用户 |

---

## 文件结构

```
tradingagents_crypto/
├── AGENTS.md                    # 项目架构决策 + 开发规范
├── docs/
│   └── sdk_findings.md          # Hyperliquid SDK 端点验证结果
└── plans/
    ├── README.md                 # 本文件（总览）
    ├── phase-1-hyperliquid.md    # Phase 1 计划
    ├── phase-2-multi-chain.md    # Phase 2 计划
    └── phase-3-risk-backtest.md  # Phase 3 计划
```

---

*详细计划见各阶段文件。*
