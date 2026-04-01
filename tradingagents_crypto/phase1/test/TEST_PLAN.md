# Phase 1 测试计划

**版本**: v1.1（修订）
**日期**: 2026-04-01
**状态**: 已批准
**负责人**: 待定
**修订说明**: v1.1 修正了单元测试数量（14→24）、补齐了 ID 不连续问题、新增 Trader Agent 测试（4个用例）、新增 Mock fixtures 完整结构、同步了 SPEC.md 的性能目标（Agent < 30s）；新增第 1.5 节"TDD 执行策略"（分层 TDD 流程 + Phase A~D 里程碑检查点）。

---

## 1. 测试策略

### 1.1 测试金字塔

```
        ┌─────────────────┐
        │   E2E 测试 (3)   │  ← 人工 + 自动化
        ├─────────────────┤
        │  集成测试 (12)    │  ← 模块间协作
        ├─────────────────┤
        │  单元测试 (24)    │  ← 模块内部逻辑
        └─────────────────┘

总计: 39 个测试用例
```

**注**: 测试 ID 按模块分组，同组内顺序递增。

### 1.2 测试原则

- **Mock 优先**：所有 HTTP 调用必须 Mock，避免真实 API 请求
- **确定性**：测试结果必须可重复
- **快速**：单元测试 < 1s，集成测试 < 30s
- **隔离**：测试之间无依赖，无共享状态

### 1.3 测试环境

| 环境 | 用途 | 说明 |
|------|------|------|
| `unit` | 单元测试 | Mock 所有外部依赖 |
| `integration` | 集成测试 | Mock HTTP，真实代码 |
| `e2e` | 端到端测试 | 真实 API（可选，人工执行） |

---

## 1.5 TDD 执行策略

**原则**：分层 TDD，先底层后上层，先单元后集成。

### 执行阶段

```
┌─────────────────────────────────────────────────────────┐
│  Phase A：纯 TDD（数据层 / 工具层 / 指标层）              │
│  ├── 1. 写 test_*.py（Red：失败）                       │
│  ├── 2. 写对应的 *.py（Green：通过）                    │
│  └── 3. Refactor → 继续下一模块                          │
│  顺序：test_utils → test_cache → test_hl_client →         │
│        test_indicators → test_schema                      │
├─────────────────────────────────────────────────────────┤
│  Phase B：Schema 测试 + Mock LLM（Agent 层）              │
│  ├── 1. 写 test_hyperliquid_analyst.py                   │
│  │   （验证 schema + 数据注入，不测语义）                  │
│  ├── 2. 实现 hyperliquid_perp_analyst.py                 │
│  └── 3. 人工评审 Prompt 质量（R-001~R-005）              │
├─────────────────────────────────────────────────────────┤
│  Phase C：集成测试优先（Graph 层）                        │
│  ├── 1. 所有层实现完成后                              │
│  ├── 2. 写 test_graph_integration.py                      │
│  └── 3. 写 test_trader_agent.py                          │
├─────────────────────────────────────────────────────────┤
│  Phase D：E2E + 人工验收                                │
│  ├── 1. 脚本：e2e_btc / eth / sol                      │
│  ├── 2. 人工评审（报告质量）                              │
│  └── 3. 性能基准测试                                     │
└─────────────────────────────────────────────────────────┘
```

### TDD 适用性

| 模块 | TDD 适用 | 原因 |
|------|---------|------|
| `utils.py` | ✅ | 纯函数，无副作用 |
| `cache.py` | ✅ | 接口清晰，Mock 简单 |
| `api.py` | ✅ | HTTP Mock 容易 |
| `indicators/` | ✅ | 计算逻辑固定 |
| `agents/schema.py` | ✅ | Pydantic 校验确定 |
| `hyperliquid_perp_analyst.py` | ⚠️ 部分 | Prompt 语义无法 TDD |
| `trader_agent.py` | ⚠️ 部分 | 决策逻辑可单元测 |
| `graph/` | ❌ | 依赖太多，集成测试更合适 |

### 提交规范

- 每次 commit 前：**所有 unit 测试必须通过**
- `pytest tests/unit/ -v --tb=short` 必须 green 才能 commit
- 集成测试在 Phase C 统一运行

### TDD 开发顺序

| 顺序 | 测试文件 | 对应实现 | 预计工时 |
|------|---------|---------|---------|
| 1 | `test_utils.py` | `utils.py` | 1.5h |
| 2 | `test_cache.py` | `cache.py` | 1h |
| 3 | `test_hl_client.py` | `api.py` | 2h |
| 4 | `test_indicators.py` | `indicators/*` | 3h |
| 5 | `test_schema.py` | `agents/schema.py` | 1h |
| 6 | `test_trader_agent.py` | `graph/trader_agent.py` | 1h |
| 7 | `test_analyst_integration.py` | `hyperliquid_perp_analyst.py` | 2h |
| 8 | `test_hl_integration.py` | `dataflows/hyperliquid/main.py` | 2h |
| 9 | `test_graph_integration.py` | `graph/*` | 2h |
| 10 | `test_config_integration.py` | `config_loader.py` | 1h |

**Phase A 合计**：~8.5h（纯 TDD）
**Phase B 合计**：~2h（Schema 测试）
**Phase C 合计**：~5h（集成测试）
**Phase D 合计**：~5h（E2E + 人工）
**总计**：~20.5h

---

## 2. 单元测试

### 2.1 数据层 — HLClient (tests/unit/test_hl_client.py)

| ID | 用例 | 输入 | 预期输出 | Mock |
|----|------|------|---------|------|
| T-001 | `get_all_mids()` 返回正确格式 | — | dict，含 "BTC" key | ✅ Mock HTTP |
| T-002 | `get_candles()` 返回 DataFrame | symbol="BTC", interval="1h" | DataFrame columns=[timestamp, open, high, low, close, volume, n_trades] | ✅ Mock HTTP |
| T-003 | `get_candles()` 时间戳转换正确 | symbol="ETH", "1h", 7 days | timestamp 为 Unix 秒（整数） | ✅ Mock HTTP |
| T-004 | `get_funding_history()` 返回列表 | symbol="BTC" | list[dict]，含 fundingRate 字段 | ✅ Mock HTTP |
| T-005 | `get_l2_snapshot()` 返回订单簿 | symbol="BTC" | dict，含 bids/asks 字段 | ✅ Mock HTTP |
| T-006 | `get_meta_and_asset_ctxs()` 返回 tuple | — | tuple，(Meta, List[PerpAssetCtx]) | ✅ Mock HTTP |

---

### 2.2 数据层 — 工具函数 (tests/unit/test_utils.py)

| ID | 用例 | 输入 | 预期输出 |
|----|------|------|---------|
| T-007 | `ms_to_dt(1710000000000)` | 毫秒 | datetime(UTC) |
| T-008 | `dt_to_ms(datetime)` | datetime | 毫秒（整数） |
| T-009 | `calc_time_range("1h", 7)` | interval, days | (start_ms, end_ms)，差距约 7×24h |
| T-010 | `calc_time_range("4h", 7)` | interval, days | (start_ms, end_ms)，差距约 7×6×4h |
| T-011 | `calc_time_range("1d", 30)` | interval, days | (start_ms, end_ms)，差距约 30 天 |
| T-012 | `retry_call` 成功 | func 正常返回 | 返回 func 结果，不重试 |
| T-013 | `retry_call` 超时重试 | func 超时 2 次后成功 | 最终返回成功结果，尝试 3 次 |

---

### 2.3 数据层 — 缓存 (tests/unit/test_cache.py)

| ID | 用例 | 输入 | 预期输出 |
|----|------|------|---------|
| T-014 | `cache.get()` 未过期 | 有效 key，未过期 | 返回缓存值 |
| T-015 | `cache.get()` 已过期 | key 存在，已超 TTL | 返回 None |
| T-016 | `cache.set()` 写入 | key, value, ttl=3600 | 写入成功 |
| T-017 | `candle_key()` 生成 | BTC, 1h, start, end | 格式化的 key 字符串 |
| T-018 | `cache` 多线程安全 | 并发读写 | 无数据损坏 |

---

### 2.4 技术指标 (tests/unit/test_indicators.py)

| ID | 用例 | 输入 | 预期输出 |
|----|------|------|---------|
| T-019 | `calc_atr()` 正确 | 标准 OHLCV DataFrame | ATR > 0 |
| T-020 | `calc_rsi()` 范围 | 标准 OHLCV DataFrame | 0 ≤ RSI ≤ 100 |
| T-021 | `calc_macd()` 返回三个值 | 标准 OHLCV DataFrame | {macd, signal, histogram} |
| T-022 | `calc_bollinger_bands()` 轨道关系 | 标准 OHLCV DataFrame | upper > middle > lower |
| T-023 | `calc_ma()` 多周期 | 标准 OHLCV DataFrame | dict 含 ma7/ma24/ma50/ma200 |
| T-024 | `calc_orderbook_imbalance()` 多头偏 | bids 总和 > asks 总和 | ratio > 1.0 |
| T-025 | `calc_orderbook_imbalance()` 空列表 | bids=[] | 返回 1.0（不崩溃） |
| T-026 | `get_trend_direction()` 上升趋势 | MA50 > MA200 | "bullish" |
| T-027 | `get_trend_direction()` 下降趋势 | MA50 < MA200 | "bearish" |
| T-028 | `calc_volatility_position()` 极端高位 | ATR% > 90% 分位 | position="extreme_high" |
| T-029 | `compute_all_indicators()` 完整 | OHLCV DataFrame | DataFrame 含所有指标列 |

---

### 2.5 Agent Schema (tests/unit/test_schema.py)

| ID | 用例 | 输入 | 预期输出 |
|----|------|------|---------|
| T-030 | `HyperliquidPerpReport` 有效 | 符合 schema 的 dict | Pydantic 校验通过 |
| T-031 | `HyperliquidPerpReport` 缺字段 | 缺少 signals | Pydantic 校验失败 |
| T-032 | `HyperliquidPerpReport` direction 无效 | direction="invalid" | Pydantic 校验失败 |
| T-033 | `HyperliquidPerpReport` confidence 越界 | confidence=1.5 | Pydantic 校验失败 |
| T-034 | `validate_report()` 降级处理 | LLM 返回缺字段 | 填充默认值，不抛异常 |

---

### 2.6 Trader Agent (tests/unit/test_trader_agent.py)

| ID | 用例 | 输入 | 预期输出 |
|----|------|------|---------|
| T-035 | `CryptoTraderAgent.decide()` 做多 | bullish=70%, bearish=20% | action="long" |
| T-036 | `CryptoTraderAgent.decide()` 做空 | bullish=20%, bearish=75% | action="short" |
| T-037 | `CryptoTraderAgent.decide()` 观望 | bullish=45%, bearish=45% | action="hold" |
| T-038 | `decide()` 输出结构完整 | 任意输入 | 包含 action/size_pct/leverage/entry_reason |

---

## 3. 集成测试

### 3.1 数据层集成 (tests/integration/test_hl_integration.py)

| ID | 用例 | 描述 | 验收条件 |
|----|------|------|---------|
| IT-001 | `get_candles()` 完整流程 | Mock HTTP + 缓存 + 时间转换 | 返回正确 DataFrame，缓存写入 |
| IT-002 | `get_current_funding()` 完整流程 | 取最近一条 funding | 返回最新费率，缓存生效 |
| IT-003 | `get_hl_data()` 聚合 | symbol + date + intervals | 返回所有数据 |
| IT-004 | `get_hl_data()` 回测模式 | backtest_mode=True | 数据按 date 正确过滤 |
| IT-005 | `get_hl_data()` 实时模式 | backtest_mode=False | date 参数不触发过滤 |

---

### 3.2 指标层集成 (tests/integration/test_indicators_integration.py)

| ID | 用例 | 描述 | 验收条件 |
|----|------|------|---------|
| IT-006 | 全指标计算流程 | OHLCV → compute_all → get_latest | 返回所有指标最新值 |
| IT-007 | atr_history 来源正确 | compute_all → calc_volatility_position | atr_history 从 df["atr"] 提取 |
| IT-008 | 指标摘要提取 | 带指标的 DataFrame | dict 包含所有必填字段 |

---

### 3.3 Agent 集成 (tests/integration/test_analyst_integration.py)

| ID | 用例 | 描述 | 验收条件 |
|----|------|------|---------|
| IT-009 | `HyperliquidPerpAnalyst` 完整调用 | Mock LLM + 真实数据转换 | 返回符合 schema 的 JSON |
| IT-010 | Prompt 包含所有数据 | 验证 Prompt 注入 | Prompt 中包含 funding/OI/指标数据 |
| IT-011 | Schema 校验通过 | LLM 返回有效 JSON | Pydantic 校验通过 |
| IT-012 | Schema 校验失败降级 | LLM 返回不完整 JSON | 填充默认值，不抛异常 |

---

### 3.4 Graph 集成 (tests/integration/test_graph_integration.py)

| ID | 用例 | 描述 | 验收条件 |
|----|------|------|---------|
| IT-013 | `CryptoTradingAgentsGraph.propagate()` | BTC + 2026-03-25 | 返回 (report, decision) |
| IT-014 | `propagate()` BTC/ETH/SOL 三个币 | 三个币种 | 均返回有效结果 |
| IT-015 | `propagate()` 回测模式 | date=2026-03-20, backtest_mode=True | 数据不包含 3-21 及之后 |
| IT-016 | `create_graph()` mode 路由 | config["mode"]="crypto" | 返回 CryptoTradingAgentsGraph |
| IT-017 | 缓存生效 | 第二次相同调用 | 响应 < 500ms |

---

### 3.5 配置层集成 (tests/integration/test_config_integration.py)

| ID | 用例 | 描述 | 验收条件 |
|----|------|------|---------|
| IT-018 | `load_config()` 加载 | 无参数 | 返回完整配置 dict |
| IT-019 | `load_config()` 合并 overrides | overrides={"mode": "stock"} | mode 覆盖成功 |
| IT-020 | `is_crypto_mode()` 判断 | crypto config / stock config | 正确返回 True/False |

---

## 4. 端到端测试

**执行方式**: 人工 + 自动化脚本混合
**执行时机**: CI 通过后，发布前

### 4.1 自动化 E2E 脚本

| ID | 脚本 | 验收条件 |
|----|------|---------|
| E2E-001 | `scripts/e2e_btc.py` | 输出 `results/btc_2026-03-25.json` |
| E2E-002 | `scripts/e2e_eth.py` | 输出 `results/eth_2026-03-25.json` |
| E2E-003 | `scripts/e2e_sol.py` | 输出 `results/sol_2026-03-25.json` |
| E2E-004 | `scripts/benchmark.py` | 输出性能报告 |

### 4.2 人工评审检查表

| # | 检查项 | 验收条件 |
|---|--------|---------|
| R-001 | JSON schema 完整性 | 报告包含所有必填字段 |
| R-002 | narrative 可读性 | 200-500 字，逻辑清晰 |
| R-003 | direction 判断有依据 | narrative 中提及具体数据 |
| R-004 | confidence 合理性 | 0.5-0.9 之间（极端情况例外）|
| R-005 | signals 阈值符合定义 | funding_rate verdict 与阈值对应 |

---

## 5. 性能测试

### 5.1 基准测试 (scripts/benchmark.py)

```python
def benchmark_propagate(symbol="BTC", runs=5):
    """
    测量指标:
    - 总耗时
    - HTTP 请求次数
    - 各阶段耗时（数据获取 / 指标 / LLM / 风控）
    - 缓存命中率
    """
```

**性能目标**:
| 指标 | 目标 | 超标阈值 |
|------|------|---------|
| HTTP 请求数 | ≤ 10 | > 15 |
| 总响应时间 | < 60s | > 90s |
| 数据获取响应 | < 5s | > 10s |
| Agent 分析响应 | < 30s | > 60s |
| 缓存命中响应 | < 500ms | > 1s |

---

## 6. 测试数据

### 6.1 Mock Fixtures

所有 Mock 数据存储在 `tests/fixtures/` 目录：

```
tests/fixtures/
├── mock_hl_api.py      # Hyperliquid API Mock
├── mock_llm.py          # LLM Mock
└── sample_data.py       # 样例 OHLCV 数据
```

### 6.2 完整 Mock LLM Response

**mock_llm_response fixture 必须包含完整嵌套结构**：

```python
@pytest.fixture
def mock_llm_response():
    return {
        "summary": "短期偏多，受资金费率支撑",
        "direction": "bullish",
        "confidence": 0.75,
        "signals": {
            "funding_rate": {
                "value": 0.0001,
                "annualized": 0.1095,
                "direction": "positive (longs pay)",
                "verdict": "normal"
            },
            "oi_trend": {
                "current": 500_000_000.0,
                "change_24h_pct": 5.2,
                "direction": "expanding",
                "verdict": "bullish"
            },
            "orderbook_imbalance": {
                "bid_depth": 1_500_000.0,
                "ask_depth": 1_200_000.0,
                "imbalance_ratio": 1.25,
                "verdict": "bullish"
            },
            "volume_anomaly": {
                "volume_24h": 1_500_000_000.0,
                "volume_ma7": 1_300_000_000.0,
                "ratio": 1.15,
                "verdict": "normal"
            },
            "volatility": {
                "atr_24h": 500.0,
                "atr_pct": 0.0075,
                "position": "medium"
            },
            "trend_4h": {
                "direction": "bullish",
                "ma_cross": "above_ma"
            },
            "trend_1d": {
                "direction": "neutral",
                "ma_cross": "above_ma"
            }
        },
        "metrics": {
            "mark_price": 67_200.0,
            "index_price": 67_180.0,
            "funding_rate": 0.0001,
            "open_interest_usd": 500_000_000.0,
            "volume_24h": 1_500_000_000.0,
            "rsi": 58.5,
            "atr": 500.0,
            "macd": 150.0,
            "macd_signal": 120.0,
            "boll_upper": 68_000.0,
            "boll_lower": 66_000.0
        },
        "narrative": "短期偏多，受资金费率正常和市场情绪支撑..."
    }
```

### 6.3 完整 Mock Meta And Asset Ctxs

```python
@pytest.fixture
def mock_meta_and_asset_ctxs():
    """返回 (Meta, List[PerpAssetCtx]) tuple — 与 SDK 实际返回格式一致"""
    meta = {
        "universe": [
            {"name": "BTC", "szDecimals": 5},
            {"name": "ETH", "szDecimals": 4},
        ]
    }
    asset_ctxs = [
        {
            "dayNtlVlm": "1234567890.0",
            "funding": "0.0001",
            "openInterest": "500000000.0",
            "prevDayPx": "66000.0",
            "markPx": "67200.0",
            "midPx": "67180.0",
            "oraclePx": "67100.0",
            "premium": "0.00005",
            "impactPxs": ["66900.0", "67500.0"],
            "dayBaseVlm": "12345.6",
        },
        {
            "dayNtlVlm": "987654321.0",
            "funding": "0.00008",
            "openInterest": "200000000.0",
            "prevDayPx": "3500.0",
            "markPx": "3550.0",
            "midPx": "3545.0",
            "oraclePx": "3540.0",
            "premium": "0.00003",
            "impactPxs": ["3520.0", "3580.0"],
            "dayBaseVlm": "9876.5",
        },
    ]
    return meta, asset_ctxs
```

---

## 7. 测试执行

### 7.1 执行命令

```bash
# 单元测试（快速）
pytest tests/unit/ -v --tb=short

# 集成测试
pytest tests/integration/ -v --tb=short

# 全部测试
pytest tests/ -v --tb=short

# 带覆盖率
pytest tests/ --cov=tradingagents_crypto --cov-report=html
```

### 7.2 CI/CD

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -v --tb=short
```

---

## 8. 测试覆盖

| 模块 | 行覆盖率目标 |
|------|------------|
| dataflows/hyperliquid/ | ≥ 80% |
| indicators/ | ≥ 90% |
| agents/ | ≥ 70% |
| graph/ | ≥ 70% |

---

## 9. 测试任务清单（TDD 顺序）

### Phase A：纯 TDD（数据层 / 工具层 / 指标层）

| ID | 任务 | 对应测试 | 预计工时 | 依赖 |
|----|------|---------|---------|------|
| A-1 | 创建 `tests/fixtures/mock_hl_api.py` | — | 1h | — |
| A-2 | 创建 `tests/fixtures/mock_llm.py` | — | 0.5h | — |
| A-3 | 创建 `tests/fixtures/sample_data.py` | — | 0.5h | — |
| A-4 | 创建 `tests/conftest.py` | — | 0.5h | A-1~3 |
| A-5 | 写 `test_utils.py` → 实现 `utils.py` | T-007~T-013 | 1.5h | A-4 |
| A-6 | 写 `test_cache.py` → 实现 `cache.py` | T-014~T-018 | 1h | A-5 |
| A-7 | 写 `test_hl_client.py` → 实现 `api.py` | T-001~T-006 | 2h | A-4 |
| A-8 | 写 `test_indicators.py` → 实现 `indicators/*` | T-019~T-029 | 3h | A-5 |
| A-9 | 写 `test_schema.py` → 实现 `agents/schema.py` | T-030~T-034 | 1h | A-4 |

**Phase A 小计**：~10.5h

### Phase B：Schema 测试 + Mock LLM（Agent 层）

| ID | 任务 | 对应测试 | 预计工时 | 依赖 |
|----|------|---------|---------|------|
| B-1 | 写 `test_analyst_integration.py` → 实现 `hyperliquid_perp_analyst.py` | IT-009~IT-012 | 2h | A-7, A-8 |
| B-2 | 写 `test_trader_agent.py` → 实现 `graph/trader_agent.py` | T-035~T-038 | 1h | A-7 |
| B-3 | 人工评审 Prompt 质量 | R-001~R-005 | 2h | B-1 |

**Phase B 小计**：~5h

### Phase C：集成测试优先（Graph 层）

| ID | 任务 | 对应测试 | 预计工时 | 依赖 |
|----|------|---------|---------|------|
| C-1 | 写 `test_hl_integration.py` → 实现 `main.py` | IT-001~IT-005 | 2h | A-6, A-7 |
| C-2 | 写 `test_graph_integration.py` → 实现 `graph/*` | IT-013~IT-017 | 2h | B-1, B-2, C-1 |
| C-3 | 写 `test_config_integration.py` → 实现 `config_loader.py` | IT-018~IT-020 | 1h | — |

**Phase C 小计**：~5h

### Phase D：E2E + 验收

| ID | 任务 | 对应测试 | 预计工时 | 依赖 |
|----|------|---------|---------|------|
| D-1 | 实现 `scripts/e2e_btc.py` | E2E-001 | 0.5h | C-2 |
| D-2 | 实现 `scripts/e2e_eth.py` | E2E-002 | 0.5h | C-2 |
| D-3 | 实现 `scripts/e2e_sol.py` | E2E-003 | 0.5h | C-2 |
| D-4 | 实现 `scripts/benchmark.py` | E2E-004 | 0.5h | C-2 |
| D-5 | 性能基准验证 | — | 1h | D-4 |
| D-6 | 人工评审（报告质量） | R-001~R-005 | 2h | D-1~D-3 |
| D-7 | 编写 `phase1_test_report.md` | — | 1h | D-6 |

**Phase D 小计**：~6h

---

**总工时**：~26.5h

---

### 里程碑检查点

| 检查点 | 通过条件 | 可进入 |
|--------|---------|--------|
| CP-A | 所有 Phase A unit 测试 green | Phase B |
| CP-B | Agent schema 测试 green + Prompt 人工评审通过 | Phase C |
| CP-C | 所有集成测试 green | Phase D |
| CP-D | E2E 脚本运行成功 + 人工评审通过 | 完成 |

---

### 快速开始命令

```bash
# 1. 进入项目目录
cd /root/TradingAgents/tradingagents_crypto

# 2. 创建虚拟环境（Phase 1 环境）
conda create -n tradingagents-crypto python=3.10
conda activate tradingagents-crypto
pip install hyperliquid-python-sdk pandas numpy ta requests tenacity pydantic pytest pytest-asyncio

# 3. Phase A：TDD 循环
# Red：写测试
pytest tests/unit/test_utils.py -v --tb=short  # 失败（代码不存在）
# Green：写代码
# 实现 utils.py
pytest tests/unit/test_utils.py -v  # 通过
# Refactor：优化（可选）
# 继续下一模块...

# 4. Phase B：Agent
pytest tests/integration/test_analyst_integration.py -v --tb=short

# 5. Phase C：Graph 集成
pytest tests/integration/test_graph_integration.py -v --tb=short

# 6. Phase D：E2E
python scripts/e2e_btc.py
```

---

## 10. 验收检查表（与 SPEC.md 8.1 对齐）

| # | 检查项 | 对应 SPEC |
|---|--------|---------|
| A-001 | `get_candles("BTC", "1h", 7)` 返回 ~168 条 | 3.1.3 |
| A-002 | `get_current_funding("BTC")` 返回 `{funding_rate, annualized}` | 3.1.4 |
| A-003 | `get_open_interest("BTC")` 解析 tuple 格式正确 | 3.1.5（修订） |
| A-004 | `get_orderbook("BTC")` 返回 `{bids, asks}` | 3.1.6 |
| A-005 | 缓存命中时响应 < 500ms | 4.1 |
| A-006 | `get_hl_data(backtest_mode=True)` 按 date 正确过滤 | 3.1.8（修订） |
| A-007 | `compute_all_indicators()` 包含所有指标列 | 3.3.1 |
| A-008 | `calc_orderbook_imbalance([])` 不崩溃 | 3.3.3 |
| A-009 | `HyperliquidPerpAnalyst.analyze()` 返回完整 JSON | 3.4.1 |
| A-010 | `direction` 在 `bullish \| bearish \| neutral` 之中 | 3.4.1 |
| A-011 | `confidence` 在 0.0-1.0 范围 | 3.4.1 |
| A-012 | Pydantic schema 校验通过 | 3.4.1 |
| A-013 | `CryptoTraderAgent.decide()` 输出结构完整 | 3.5.2 |
| A-014 | `propagate()` 返回 tuple(dict, str) | 3.5.1 |
| A-015 | `final_decision` 在 `long \| short \| hold \| close` 之中 | 3.5.1 |
| A-016 | `create_graph(config)` 根据 mode 返回正确实例 | 3.2.2 |
| A-017 | BTC / ETH / SOL 三币种全部跑通 | 3.5.1 |
| A-018 | 单次 propagate() HTTP ≤ 10 次 | 4.1 |
| A-019 | 回测模式无未来数据泄露 | 4.2 |
| A-020 | API 限流时重试成功 | 4.2 |

---

*本测试计划为 Phase 1 测试执行的基准文件。任何变更需更新本文件并同步 SPEC.md。*
