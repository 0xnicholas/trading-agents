# Phase 4: 测试计划

## 测试策略

### 分层测试

| 层级 | 范围 | 网络依赖 | Mock策略 |
|------|------|---------|---------|
| Unit | 单个模块 | ❌ 无 | ✅ Mock 外部依赖 |
| Integration | 多模块协作 | ⚠️ 最小化 | Mock HTTP |
| E2E | 完整流程 | ✅ 真实 | ❌ 不 mock |

---

## Phase 4B 测试

### M4.1 结构化日志

| ID | 测试内容 | 输入 | 预期结果 |
|----|---------|------|---------|
| T_LOG_01 | JSONFormatter 输出正确 | log record | 有效 JSON，包含所有字段 |
| T_LOG_02 | trace_id 传递 | context with trace_id | 日志包含 trace_id |
| T_LOG_03 | 异常序列化 | Exception | 异常消息正确序列化 |
| T_LOG_04 | 日志轮转 | > 10MB | 新文件创建，旧文件归档 |

### M4.2 健康检查

| ID | 测试内容 | 输入 | 预期结果 |
|----|---------|------|---------|
| T_HEALTH_01 | /health 返回 healthy | 无 | status=healthy, 200 |
| T_HEALTH_02 | /health/ready 检查失败 | API 不可用 | status=degraded, 200 |
| T_HEALTH_03 | /health/live | 无 | status=live, 200 |

### M4.3 Prometheus Metrics

| ID | 测试内容 | 输入 | 预期结果 |
|----|---------|------|---------|
| T_METRICS_01 | Counter 增加 | 触发交易 | orders_total 增加 |
| T_METRICS_02 | Histogram 记录 | API 调用 | request_duration_seconds 记录 |
| T_METRICS_03 | Gauge 设置 | 持仓变化 | position_size 更新 |
| T_METRICS_04 | /metrics 端点 | GET /metrics | 包含所有指标 |

### M4.4 告警系统

| ID | 测试内容 | 输入 | 预期结果 |
|----|---------|------|---------|
| T_ALERT_01 | Webhook 发送 | 触发告警 | Discord 收到消息 |
| T_ALERT_02 | 连续亏损检测 | N笔亏损（可配置） | 告警触发 |
| T_ALERT_03 | API 错误率检测 | X% 错误（可配置） | 告警触发 |
| T_ALERT_04 | 告警去重 | 同一告警 1min 内 | 只发一次 |
| T_ALERT_05 | 阈值可配置 | 修改配置 | 新阈值生效 |

### M4.5 Docker

| ID | 测试内容 | 输入 | 预期结果 |
|----|---------|------|---------|
| T_DOCKER_01 | 镜像构建 | docker build | 构建成功 |
| T_DOCKER_02 | 容器启动 | docker-compose up | 容器运行 |
| T_DOCKER_03 | 健康检查 | curl localhost:8000/health | 200 OK |
| T_DOCKER_04 | 日志输出 | docker logs | JSON 格式日志 |

### M4.6 CI/CD

| ID | 测试内容 | 输入 | 预期结果 |
|----|---------|------|---------|
| T_CICD_01 | PR 检查 | push to PR | 测试运行 |
| T_CICD_02 | Main 检查 | push to main | Docker 构建 |
| T_CICD_03 | Coverage 检查 | coverage < 80% | 构建失败 |

---

## Phase 4A 测试

### M4.7 Agent 工厂

| ID | 测试内容 | 输入 | 预期结果 |
|----|---------|------|---------|
| T_FACTORY_01 | 创建 BTC Analyst | factory.create_analyst("btc") | Analyst 实例 |
| T_FACTORY_02 | 创建 Trader | factory.create_trader("crypto") | Trader 实例 |
| T_FACTORY_03 | 未知类型报错 | factory.create_analyst("unknown") | ValueError |

### M4.8 共享 Memory

| ID | 测试内容 | 输入 | 预期结果 |
|----|---------|------|---------|
| T_MEMORY_01 | 读写操作 | write + read | 读写一致 |
| T_MEMORY_02 | 并发写入 | 2线程同时写 | 无数据丢失 |
| T_MEMORY_03 | 读写锁 | 1写 2读并发 | 无死锁 |
| T_MEMORY_04 | trace_id 隔离 | 2个 trace | 状态不混淆 |
| T_MEMORY_05 | asyncio.Lock | async context | 正常读写 |

### M4.9 Meta-Agent

| ID | 测试内容 | 输入 | 预期结果 |
|----|---------|------|---------|
| T_META_01 | 任务分解 | 用户请求 | 分解为子任务 |
| T_META_02 | 任务分发 | 子任务列表 | 分发给正确 Agent |
| T_META_03 | 结果聚合 | 多个 Analyst 结果 | 汇总报告 |
| T_META_04 | 异常处理 | Analyst 超时 | 降级处理 |

### M4.10 并行执行

| ID | 测试内容 | 输入 | 预期结果 |
|----|---------|------|---------|
| T_PARALLEL_01 | 4 Analyst 并行 | 4个分析请求 | 全部完成 |
| T_PARALLEL_02 | 单个失败 | 1个 Analyst 异常 | 其他 3个完成 |
| T_PARALLEL_03 | 超时处理 | Analyst > 30s | 超时中断 |
| T_PARALLEL_04 | 加速比 | 并行 vs 顺序 | 加速比 > 3x |
| T_PARALLEL_05 | 顺序正确 | 4个 Analyst | 结果顺序一致 |

---

## Phase 4C 测试

### M4.11 Paper Trading

| ID | 测试内容 | 输入 | 预期结果 |
|----|---------|------|---------|
| T_PAPER_01 | 模拟开仓 | market_order(long, 10000) | 持仓增加 |
| T_PAPER_02 | 模拟平仓 | close_position | 持仓减少，PNL 正确 |
| T_PAPER_03 | 模拟滑点 | 大订单 | 滑点计算正确 |
| T_PAPER_04 | 资金费率 | 持仓 24h | 资金费率扣除 |
| T_PAPER_05 | 模式切换 | backtest → paper | 配置正确 |

### M4.12 实盘连接

| ID | 测试内容 | 输入 | 预期结果 |
|----|---------|------|---------|
| T_LIVE_01 | 连接测试 | 有效 API key | 连接成功 |
| T_LIVE_02 | 下单测试 | 测试网下单 | 订单 ID 返回 |
| T_LIVE_03 | 查询持仓 | 已有持仓 | 持仓信息正确 |
| T_LIVE_04 | 取消订单 | 未成交订单 | 取消成功 |

### M4.13 人工审批

| ID | 测试内容 | 输入 | 预期结果 |
|----|---------|------|---------|
| T_APPROVAL_01 | 审批消息格式 | 交易信号 | Discord 消息格式正确 |
| T_APPROVAL_02 | 审批超时 | 5min 无响应 | 自动 reject |
| T_APPROVAL_03 | 审批通过 | 用户点击 approve | 订单执行 |
| T_APPROVAL_04 | 审批拒绝 | 用户点击 reject | 订单不执行 |
| T_APPROVAL_05 | 审批日志 | 所有操作 | 记录到日志 |

---

## 测试环境要求

### Mock 对象
```python
# HTTP Mock
@pytest.fixture
def mock_hl_api():
    with responses.RequestsMock() as rsps:
        rsps.add(
            rsps.GET,
            "https://api.hyperliquid.xyz/info",
            json={"status": "ok"},
            status=200,
        )
        yield rsps

# Webhook Mock
@pytest.fixture
def mock_discord_webhook():
    with responses.RequestsMock() as rsps:
        rsps.add(
            rsps.POST,
            "https://discord.com/api/webhooks/...",
            json={"id": "123"},
            status=200,
        )
        yield rsps
```

### 合成数据
```python
# 日志合成
def generate_log_record():
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "level": random.choice(["INFO", "WARNING", "ERROR"]),
        "service": "crypto-trading",
        "module": random.choice(["backtest", "agent", "trading"]),
        "message": "Test message",
        "trace_id": uuid.uuid4().hex[:8],
    }
```

---

## 覆盖率目标

| 模块 | 行覆盖率 | 分支覆盖 |
|------|---------|---------|
| utils/logging | ≥ 90% | ≥ 80% |
| api/health | ≥ 95% | ≥ 90% |
| memory/ | ≥ 85% | ≥ 75% |
| graph/nodes/meta_agent | ≥ 80% | ≥ 70% |
| trading/modes/paper | ≥ 85% | ≥ 75% |

---

## 测试执行

```bash
# 运行所有 Phase 4 测试
cd /root/TradingAgents
python3 -m pytest tradingagents_crypto/tests/unit/test_logging.py -v
python3 -m pytest tradingagents_crypto/tests/unit/test_health.py -v
python3 -m pytest tradingagents_crypto/tests/unit/test_metrics.py -v
python3 -m pytest tradingagents_crypto/tests/unit/test_factory.py -v
python3 -m pytest tradingagents_crypto/tests/unit/test_memory.py -v
python3 -m pytest tradingagents_crypto/tests/unit/test_meta_agent.py -v

# 集成测试
python3 -m pytest tradingagents_crypto/tests/integration/test_paper_trading.py -v
python3 -m pytest tradingagents_crypto/tests/integration/test_live_trading.py -v
```

---

## 修订历史

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-04-02 | v1.0 | 初始版本 |
