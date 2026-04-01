# M1.7：端到端测试

**状态**: 🔵 就绪（未开始）
**周期**: Day 16-21
**前置依赖**: M1.6 ✅（Graph 集成）

---

## 任务目标

完成 Phase 1 全链路端到端测试，验证 `propagate("BTC", date)` 完整流程，输出符合 Schema 的分析报告。

---

## 详细子任务

### T1.7.1 BTC-PERP 端到端测试
- [ ] `scripts/e2e_btc.py` — BTC 完整分析
  ```python
  from tradingagents_crypto.graph import create_graph
  from tradingagents_crypto.default_config import load_config
  
  config = load_config()
  graph = create_graph(config)
  
  _, decision = graph.propagate("BTC", "2026-03-25")
  print("Decision:", decision)
  
  # 保存结果
  with open("results/btc_2026-03-25.json", "w") as f:
      json.dump({"analysis": analyst_report, "decision": decision}, f, indent=2)
  ```
- [ ] 运行脚本，验证输出
- [ ] 人工评审分析报告质量

### T1.7.2 ETH-PERP 端到端测试
- [ ] `scripts/e2e_eth.py`
  - 同上，测试 ETH 交易对
  - 验证跨币种泛化能力

### T1.7.3 SOL-PERP 端到端测试
- [ ] `scripts/e2e_sol.py`
  - 同上，测试 SOL 交易对
  - 验证币种无关性

### T1.7.4 回测模式测试
- [ ] `tests/test_backtest_mode.py`
  - 设置 `curr_date = "2026-03-20"`
  - 运行 `propagate("BTC", "2026-03-20")`
  - 验证返回数据中 **不包含** 3-21 及之后的数据
  - 确保无未来数据泄露

### T1.7.5 缓存测试
- [ ] `tests/test_cache.py`
  - 连续两次相同调用
  - 第二次验证走缓存（< 100ms）
  - 缓存命中日志验证

### T1.7.6 API 限流降级测试
- [ ] `tests/test_rate_limit.py`
  - Mock HTTP 429 响应
  - 验证 tenacity 重试逻辑
  - 验证最终成功返回（修复后）

### T1.7.7 性能基准
- [ ] `scripts/benchmark.py`
  - 单次 `propagate()` HTTP 请求次数统计
  - 各步骤耗时分析（数据获取 / 指标计算 / LLM 调用 / 风险评估）
  - 内存占用监控

### T1.7.8 人工评审
- [ ] 输出报告格式评审
  - JSON schema 是否完整
  - narrative 是否专业、有逻辑
  - signals/metrics 数值是否合理
- [ ] LLM 分析质量评审
  - direction 判断是否有依据
  - confidence 评分是否合理
  - 反驳点是否有力

### T1.7.9 测试报告
- [ ] `docs/phase1_test_report.md`
  ```markdown
  # Phase 1 端到端测试报告
  
  ## 测试环境
  - Python: 3.10
  - Hyperliquid API: MAINNET
  - 测试日期: 2026-04-01
  
  ## 测试用例结果
  | 用例 | 状态 | 响应时间 | 说明 |
  |------|------|---------|------|
  | BTC-PERP 完整分析 | ✅ | 12s | ... |
  | ETH-PERP 完整分析 | ✅ | 11s | ... |
  | SOL-PERP 完整分析 | ✅ | 13s | ... |
  | 回测模式 | ✅ | 10s | 无数据泄露 |
  | 缓存命中 | ✅ | 0.3s | ... |
  | 限流降级 | ✅ | 15s | 重试3次成功 |
  
  ## API 调用统计
  - 单次 propagate(): 平均 7 次 HTTP
  
  ## 已知问题
  - [ ] ...
  
  ## 结论
  - ✅ Phase 1 通过验收
  - 可启动 Phase 2
  ```

---

## 交付物

| 文件 | 说明 |
|------|------|
| `scripts/e2e_btc.py` | BTC 端到端脚本 |
| `scripts/e2e_eth.py` | ETH 端到端脚本 |
| `scripts/e2e_sol.py` | SOL 端到端脚本 |
| `scripts/benchmark.py` | 性能基准脚本 |
| `tests/test_backtest_mode.py` | 回测模式测试 |
| `tests/test_cache.py` | 缓存测试 |
| `tests/test_rate_limit.py` | 限流降级测试 |
| `docs/phase1_test_report.md` | 测试报告 |

---

## 验收标准

| 测试用例 | 验收条件 |
|---------|---------|
| BTC 完整分析 | 返回包含 `summary` / `direction` / `signals` 的 JSON |
| ETH 完整分析 | 同上 |
| SOL 完整分析 | 同上 |
| 回测模式 | 数据不含未来日期 |
| 缓存命中 | 第二次调用 < 100ms |
| 限流降级 | 重试后成功返回 |
| HTTP 调用 | 单次 ≤ 10 次 |
| 响应时间 | 数据获取 < 5s，Agent < 30s |

---

## 预计工时

| 子任务 | 预计时间 |
|--------|---------|
| T1.7.1-3 BTC/ETH/SOL 脚本 | 2 小时 |
| T1.7.4 回测模式 | 1 小时 |
| T1.7.5 缓存测试 | 1 小时 |
| T1.7.6 限流测试 | 1 小时 |
| T1.7.7 性能基准 | 1 小时 |
| T1.7.8 人工评审 | 2 小时 |
| T1.7.9 测试报告 | 1 小时 |
| **合计** | **~9 小时（1.5 天）** |
