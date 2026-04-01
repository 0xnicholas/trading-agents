# Phase 2：ETH / Solana 多链扩展

**状态**: 🔵 待启动
**预计周期**: 14 工作日 (Day 1-21)

---

## 交付物索引

### 规格文档
| 文件 | 说明 |
|------|------|
| `phase2/spec/SPEC.md` | 技术规格说明书 (v1.0) |
| `phase2/test/TEST_PLAN.md` | 测试计划 (v1.0) |

### 任务定义
| 文件 | 说明 |
|------|------|
| `tasks/phase2/TASK.md` | 详细任务分解 (65 tasks) |
| `tasks/phase2/KANBAN.md` | Kanban 看版 |

### 计划文档
| 文件 | 说明 |
|------|------|
| `plans/phase-2-multi-chain.md` | 原始 Phase 2 计划 |

---

## 里程碑

| Day | 里程碑 | 任务数 |
|-----|--------|--------|
| 1-2 | M2.0 数据源验证 | 7 |
| 3-6 | M2.1 ETH 数据层 + M2.3 ETH Analyst | 20 |
| 4-10 | M2.2 SOL 数据层 + M2.4 SOL Analyst | 14 |
| 11-14 | M2.5 Macro Analyst | 13 |
| 15-18 | M2.6 Graph 升级 | 6 |
| 19-21 | M2.7 集成测试 | 6 |

---

## 快速开始

### 1. 启动 M2.0 数据源验证

```bash
cd /root/TradingAgents

# 验证 CoinGecko API
curl "https://api.coingecko.com/api/v3/global" | jq

# 验证 Alternative.me API
curl "https://api.alternative.me/v2/fng/" | jq

# 验证 Binance Futures API
curl "https://fapi.binance.com/fapi/v1/fundingRate?symbol=ETHUSDT" | jq

# 验证 Jupiter API
curl "https://api.jup.ag/v1/price?ids=SOL&vsToken=USDT" | jq
```

### 2. 运行测试

```bash
# 安装依赖
pip install responses httpretty pytest-cov

# 运行测试
python3 -m pytest tradingagents_crypto/tests/ -v
```

---

## 核心数据流

```
CoinGecko ─────┐
               │
Binance ───────┼──► ETH Data ──► ETH Analyst ──┐
               │                                   │
Etherscan ─────┤                                   │
               ├──► Macro Data ──► Macro Analyst ─┼──► Trader ──► Decision
               │                                   │
Jupiter ───────┤                                   │
               │                                   │
GeckoTerminal ─┴──► SOL Data ──► SOL Analyst ──────┘
```

---

## 关键设计

### 置信度体系

| 等级 | 值 | 来源 |
|------|---|------|
| 高 | 0.9-1.0 | 官方 SDK/API |
| 中 | 0.7-0.8 | 免费但稳定 |
| 低 | 0.4-0.6 | 近似/代理数据 |
| 估算 | 0.3-0.5 | 免费但不稳定 |

### 降级策略

单链失败时：
1. 返回降级数据 (`status: "degraded"`)
2. 置信度自动下调 0.1-0.3
3. 其他链继续正常运行

---

## 联系人

- 项目 Lead: @0xnicholas
- Phase 1 完成: 2026-04-01
