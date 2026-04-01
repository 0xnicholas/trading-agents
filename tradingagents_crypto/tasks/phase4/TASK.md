# Phase 4: 任务分解

## 阶段 B: Production Infrastructure

### M4.1: 结构化日志系统

| 任务 | 说明 | 验收标准 |
|------|------|---------|
| T4.1.1 | 创建 `utils/logging.py`，实现 JSONFormatter | 所有日志输出 JSON 格式 |
| T4.1.2 | 更新所有模块使用结构化日志 | `logger.info("Position opened", extra={"symbol": "BTC"})` |
| T4.1.3 | 添加 trace_id 支持 | 日志可追踪跨模块请求 |
| T4.1.4 | 日志轮转配置（按天切割） | 日志文件每天一个新文件 |

### M4.2: 健康检查端点

| 任务 | 说明 | 验收标准 |
|------|------|---------|
| T4.2.1 | 创建 FastAPI 健康检查端点 | GET /health 返回 JSON |
| T4.2.2 | 实现 /health/ready 检查 | 检查所有依赖服务 |
| T4.2.3 | 实现 /health/live | Kubernetes liveness probe |

### M4.3: Prometheus Metrics

| 任务 | 说明 | 验收标准 |
|------|------|---------|
| T4.3.1 | 创建 metrics 模块 | `prometheus_client` 集成 |
| T4.3.2 | 实现交易指标（orders/pnl/win_rate） | 交易触发指标更新 |
| T4.3.3 | 实现性能指标（响应时间/API延迟） | 中间件自动记录 |
| T4.3.4 | 实现缓存命中率指标 | cache hit/miss 自动记录 |
| T4.3.5 | 添加 /metrics 端点 | Prometheus 可抓取 |

### M4.4: 告警系统

| 任务 | 说明 | 验收标准 |
|------|------|---------|
| T4.4.1 | 实现 Webhook 客户端 | Discord/Slack 支持 |
| T4.4.2 | 实现告警规则引擎 | 规则可配置 |
| T4.4.3 | 实现连续亏损告警 | 5笔亏损触发告警 |
| T4.4.4 | 实现 API 错误率告警 | >10% 触发 |
| T4.4.5 | 实现磁盘空间告警 | <1GB 触发 |

### M4.5: Docker 化部署

| 任务 | 说明 | 验收标准 |
|------|------|---------|
| T4.5.1 | 创建 Dockerfile | Python 3.11, 非 root 用户 |
| T4.5.2 | 创建 docker-compose.yml | 包含所有依赖服务 |
| T4.5.3 | 创建 .dockerignore | 排除测试/文档 |
| T4.5.4 | 多阶段构建优化 | 最终镜像 < 500MB |

### M4.6: CI/CD 流程

| 任务 | 说明 | 验收标准 |
|------|------|---------|
| T4.6.1 | 创建 GitHub Actions workflow | push 时自动运行 |
| T4.6.2 | 添加 pytest 步骤 | 全部测试通过 |
| T4.6.3 | 添加 ruff lint 检查 | 无 lint 错误 |
| T4.6.4 | 添加 Docker build 步骤 | 镜像构建成功 |
| T4.6.5 | 配置 pytest coverage | >80% 覆盖率 |

---

## 阶段 A: Multi-Agent Orchestration

### M4.7: Agent 工厂模式重构

| 任务 | 说明 | 验收标准 |
|------|------|---------|
| T4.7.1 | 创建 `agents/factory.py` | 工厂函数创建 Agent |
| T4.7.2 | 重构 Analyst 接口 | 支持 async 调用 |
| T4.7.3 | 重构 Trader 接口 | 支持 async 调用 |
| T4.7.4 | 工厂函数注册表 | 可扩展新 Agent |

### M4.8: 共享 Memory

| 任务 | 说明 | 验收标准 |
|------|------|---------|
| T4.8.1 | 创建 `memory/shared_state.py` | SharedState dataclass |
| T4.8.2 | 实现读写锁 | 线程安全 |
| T4.8.3 | 实现跨 Agent 状态同步 | 多 Agent 可读写同一状态 |
| T4.8.4 | 实现状态持久化 | 可选 Redis 存储 |

### M4.9: Meta-Agent

| 任务 | 说明 | 验收标准 |
|------|------|---------|
| T4.9.1 | 创建 `graph/nodes/meta_agent.py` | 任务分解逻辑 |
| T4.9.2 | 实现任务分发机制 | 分发给子 Analyst |
| T4.9.3 | 创建 `graph/nodes/analyst_coordinator.py` | 协调多个 Analyst |
| T4.9.4 | 实现结果聚合逻辑 | 汇总分析报告 |
| T4.9.5 | 更新 `crypto_trading_graph.py` | 新的 graph 结构 |

### M4.10: 并行 Analyst 执行

| 任务 | 说明 | 验收标准 |
|------|------|---------|
| T4.10.1 | 实现 async Analyst | 所有 Analyst 支持 async |
| T4.10.2 | 实现并行调用 | `asyncio.gather` |
| T4.10.3 | 实现错误处理 | 单个失败不影响整体 |
| T4.10.4 | 添加超时控制 | 单个 Analyst 超时 30s |
| T4.10.5 | 性能测试 | 并行 vs 顺序 加速比 >3x |

---

## 阶段 C: Live Trading

### M4.11: Paper Trading 模式

| 任务 | 说明 | 验收标准 |
|------|------|---------|
| T4.11.1 | 创建 `trading/modes/paper_trader.py` | 模拟 Hyperliquid API |
| T4.11.2 | 实现模拟订单簿 | 模拟深度/滑点 |
| T4.11.3 | 实现资金费率模拟 | 8h 自动计费 |
| T4.11.4 | 实现持仓管理 | 模拟仓位更新 |
| T4.11.5 | 模式切换配置 | `mode="paper"` 激活 |

### M4.12: 实盘 API 连接

| 任务 | 说明 | 验收标准 |
|------|------|---------|
| T4.12.1 | 创建 `trading/connectors/hyperliquid_connector.py` | 实盘连接器 |
| T4.12.2 | 实现订单接口 | 市价单/限价单 |
| T4.12.3 | 实现查询接口 | 持仓/订单状态 |
| T4.12.4 | 实现取消接口 | 订单取消 |
| T4.12.5 | 添加重试机制 | 超时自动重试 |

### M4.13: 人工审批流程

| 任务 | 说明 | 验收标准 |
|------|------|---------|
| T4.13.1 | 创建审批消息格式 | Discord/Slack 格式 |
| T4.13.2 | 实现审批状态机 | pending/approved/rejected |
| T4.13.3 | 实现超时处理 | 5分钟无响应 = reject |
| T4.13.4 | Webhook 集成 | Discord webhook |
| T4.13.5 | 审批日志记录 | 所有审批操作记录 |

---

## 实施顺序（修正）

> 注意：M4.13 人工审批应早于 M4.11

```
Phase 4B (基础设施)
├── M4.1 结构化日志
├── M4.2 健康检查
├── M4.3 Prometheus Metrics
├── M4.4 告警系统
├── M4.5 Docker 化
└── M4.6 CI/CD

Phase 4A (多 Agent)
├── M4.7 Agent 工厂
├── M4.8 共享 Memory
├── M4.9 Meta-Agent
└── M4.10 并行执行

Phase 4C (实盘)
├── M4.13 人工审批  ← 提前
├── M4.11 Paper Trading
└── M4.12 实盘连接
```
