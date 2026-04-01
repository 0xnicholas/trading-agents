# Phase 1 — Hyperliquid 单链打样

**状态**: 进行中
**周期**: 2-3 周
**目标**: 跑通完整 Crypto 版 TradingAgents pipeline

---

## 交付物清单

| 类别 | 文件 | 说明 |
|------|------|------|
| 规格 | `spec/SPEC.md` | 完整功能规格说明书 |
| 测试 | `test/TEST_PLAN.md` | 测试计划和用例定义 |
| 进度 | `../STATUS.md` | 项目整体状态 |
| 任务 | `../tasks/m1_*-*/TASK.md` | 各里程碑详细任务 |
| 计划 | `../plans/phase-1-hyperliquid.md` | Phase 1 原始计划 |

---

## 快速导航

### 开发
- **规格说明书** → `spec/SPEC.md`
- **开发任务** → `../tasks/m1_*-env/` 等

### 测试
- **测试计划** → `test/TEST_PLAN.md`
- **测试用例**: 24 个（14 单元 + 7 集成 + 3 E2E）

### 验收
- **验收检查表** → `spec/SPEC.md` 第 8 节
- **测试报告** → 待完成（测试后）

---

## 里程碑

| M | 名称 | 状态 | 关键交付物 |
|---|------|------|-----------|
| M1.0 | SDK 验证 | ✅ 完成 | `docs/sdk_findings.md` |
| M1.1 | 环境搭建 | 🔵 待启动 | 虚拟环境 + 目录结构 |
| M1.2 | 数据层 | 🔵 待启动 | `dataflows/hyperliquid/*.py` |
| M1.3 | 配置层 | 🔵 待启动 | `default_config.py` |
| M1.4 | 技术指标 | 🔵 待启动 | `indicators/*.py` |
| M1.5 | Agent 层 | 🔵 待启动 | `HyperliquidPerpAnalyst` |
| M1.6 | Graph 集成 | 🔵 待启动 | `CryptoTradingAgentsGraph` |
| M1.7 | 端到端测试 | 🔵 待启动 | 测试报告 |

---

## 目录结构

```
phase1/
├── README.md           # 本文件
├── spec/
│   └── SPEC.md         # 完整规格说明书
└── test/
    └── TEST_PLAN.md     # 测试计划
```

---

## 启动条件

M1.1 就绪，可随时开始。

---

## 联系人

待定
