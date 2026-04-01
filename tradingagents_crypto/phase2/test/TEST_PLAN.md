# Phase 2 测试计划

**版本**: v1.0
**日期**: 2026-04-01
**状态**: 待审查

---

## 1. 测试策略

### 1.1 测试金字塔

```
        ┌─────────────┐
        │     E2E     │   ← 3 tests (多链并行分析)
        ├─────────────┤
        │ Integration │   ← 12 tests (数据层 + Analyst)
        ├─────────────┤
        │    Unit     │   ← 45 tests (各模块独立)
        └─────────────┘
```

### 1.2 测试覆盖率目标

| 模块 | 目标覆盖率 |
|------|-----------|
| dataflows/ethereum | 80% |
| dataflows/solana | 80% |
| dataflows/macro | 75% |
| agents/analysts | 70% |
| graph | 80% |

---

## 2. 单元测试 (45 tests)

### 2.1 Ethereum 数据层 (12 tests)

#### price.py (T2.1.1)

| ID | 测试名称 | 验证内容 |
|----|---------|---------|
| U-ETH-PRICE-01 | `test_get_eth_price_success` | 成功获取 ETH 价格 |
| U-ETH-PRICE-02 | `test_get_eth_price_cached` | 缓存生效 |
| U-ETH-PRICE-03 | `test_check_price_deviation_normal` | 偏差 < 1% 正常 |
| U-ETH-PRICE-04 | `test_check_price_deviation_warning` | 偏差 > 1% 警告 |

#### funding.py (T2.1.4)

| ID | 测试名称 | 验证内容 |
|----|---------|---------|
| U-ETH-FUND-01 | `test_get_binance_funding_success` | 成功获取 Binance 资金费率 |
| U-ETH-FUND-02 | `test_get_binance_funding_annualized` | 年化计算正确 |
| U-ETH-FUND-03 | `test_get_binance_funding_confidence` | 置信度 0.9 |

#### onchain.py (T2.1.7-2.1.10)

| ID | 测试名称 | 验证内容 |
|----|---------|---------|
| U-ETH-GAS-01 | `test_get_gas_price_success` | 成功获取 Gas 价格 |
| U-ETH-GAS-02 | `test_gas_sentiment_calculation` | Gas 情绪计算 |
| U-ETH-STAKING-01 | `test_get_staking_ratio` | 质押率获取 |
| U-ETH-DEFI-01 | `test_get_defi_tvl` | TVL 获取 |
| U-ETH-ONCHAIN-01 | `test_eth_onchain_all` | 全部链上数据整合 |

### 2.2 Solana 数据层 (10 tests)

#### price.py (T2.2.1)

| ID | 测试名称 | 验证内容 |
|----|---------|---------|
| U-SOL-PRICE-01 | `test_get_sol_price_success` | 成功获取 SOL 价格 |
| U-SOL-PRICE-02 | `test_get_sol_price_24h_change` | 24h 变化率 |

#### dex.py (T2.2.2-2.2.3)

| ID | 测试名称 | 验证内容 |
|----|---------|---------|
| U-SOL-DEX-01 | `test_get_dex_liquidity_jupiter` | Jupiter 流动性 |
| U-SOL-DEX-02 | `test_get_dex_liquidity_raydium_fallback` | Raydium 备选 |
| U-SOL-DEX-03 | `test_get_dex_liquidity_combined` | 总 TVL 计算 |

#### meme.py (T2.2.4-2.2.5)

| ID | 测试名称 | 验证内容 |
|----|---------|---------|
| U-SOL-MEME-01 | `test_get_meme_coins_success` | Meme 币列表 |
| U-SOL-MEME-02 | `test_get_meme_coins_top_5` | Top 5 排序 |
| U-SOL-MEME-03 | `test_meme_turnover_calculation` | 周转率计算 |

### 2.3 Macro 数据层 (10 tests)

#### btc_dominance.py (T2.5.1-2.5.2)

| ID | 测试名称 | 验证内容 |
|----|---------|---------|
| U-MACRO-BTC-01 | `test_get_btc_dominance_success` | BTC.D 获取 |
| U-MACRO-BTC-02 | `test_btc_dominance_trend_7d` | 7d 趋势计算 |

#### fear_greed.py (T2.5.3)

| ID | 测试名称 | 验证内容 |
|----|---------|---------|
| U-MACRO-FG-01 | `test_get_fear_greed_success` | Fear & Greed 获取 |
| U-MACRO-FG-02 | `test_fear_greed_confidence_low` | 置信度 0.5 |
| U-MACRO-FG-03 | `test_fear_greed_label_mapping` | 标签映射正确 |

#### stablecoin_flow.py (T2.5.4-2.5.5)

| ID | 测试名称 | 验证内容 |
|----|---------|---------|
| U-MACRO-SC-01 | `test_get_stablecoin_flow_success` | 稳定币流获取 |
| U-MACRO-SC-02 | `test_stablecoin_flow_proxy_calculation` | 代理指标计算 |
| U-MACRO-SC-03 | `test_stablecoin_flow_confidence_low` | 置信度 0.5 |

#### correlation.py (T2.5.6-2.5.10)

| ID | 测试名称 | 验证内容 |
|----|---------|---------|
| U-MACRO-CORR-01 | `test_get_price_history_7d` | 7d 价格历史 |
| U-MACRO-CORR-02 | `test_pearson_correlation` | Pearson 相关系数 |
| U-MACRO-CORR-03 | `test_correlation_verdict` | 相关性判断 |

### 2.4 Agent Analysts (8 tests)

#### ethereum_onchain_analyst.py (T2.3.1, T2.3.7)

| ID | 测试名称 | 验证内容 |
|----|---------|---------|
| U-AGENT-ETH-01 | `test_eth_analyst_schema_validation` | Pydantic Schema 验证 |
| U-AGENT-ETH-02 | `test_eth_analyst_gas_sentiment` | Gas 情绪信号 |
| U-AGENT-ETH-03 | `test_eth_analyst_funding_diff` | 资金费率对比信号 |

#### solana_dex_analyst.py (T2.4.1, T2.4.6)

| ID | 测试名称 | 验证内容 |
|----|---------|---------|
| U-AGENT-SOL-01 | `test_sol_analyst_schema_validation` | Pydantic Schema 验证 |
| U-AGENT-SOL-02 | `test_sol_analyst_meme_signals` | Meme 币信号 |

#### cross_chain_macro_analyst.py (T2.5.11, T2.5.12)

| ID | 测试名称 | 验证内容 |
|----|---------|---------|
| U-AGENT-MACRO-01 | `test_macro_analyst_schema_validation` | Pydantic Schema 验证 |
| U-AGENT-MACRO-02 | `test_macro_analyst_regime_detection` | 市场 regime 检测 |
| U-AGENT-MACRO-03 | `test_macro_analyst_confidence_weighting` | 置信度加权 |

### 2.5 Graph 升级 (5 tests)

#### crypto_trading_graph.py (T2.6.1-2.6.6)

| ID | 测试名称 | 验证内容 |
|----|---------|---------|
| U-GRAPH-01 | `test_multi_chain_config` | 多链配置解析 |
| U-GRAPH-02 | `test_parallel_chain_execution` | 并行执行逻辑 |
| U-GRAPH-03 | `test_trader_multi_chain_summary` | 多链汇总决策 |
| U-GRAPH-04 | `test_chain_failure_graceful` | 单链失败降级 |
| U-GRAPH-05 | `test_confidence_deduction_on_error` | 错误时置信度下调 |

---

## 3. 集成测试 (12 tests)

### 3.1 数据层集成 (6 tests)

| ID | 测试名称 | 验证内容 | 依赖 |
|----|---------|---------|------|
| I-DATA-01 | `test_eth_data_layer_integration` | ETH 数据层完整流程 | T2.1.11 |
| I-DATA-02 | `test_sol_data_layer_integration` | SOL 数据层完整流程 | T2.2.6 |
| I-DATA-03 | `test_macro_data_layer_integration` | Macro 数据层完整流程 | T2.5.11 |
| I-DATA-04 | `test_cross_chain_data_freshness` | 多链数据一致性 | — |
| I-DATA-05 | `test_cache_shared_across_chains` | 跨链缓存共享 | — |
| I-DATA-06 | `test_rate_limit_handling` | 限流处理 | — |

### 3.2 Agent 集成 (4 tests)

| ID | 测试名称 | 验证内容 | 依赖 |
|----|---------|---------|------|
| I-AGENT-01 | `test_eth_analyst_with_real_data` | ETH Analyst 真实数据 | T2.3.8 |
| I-AGENT-02 | `test_sol_analyst_with_real_data` | SOL Analyst 真实数据 | T2.4.7 |
| I-AGENT-03 | `test_macro_analyst_with_real_data` | Macro Analyst 真实数据 | T2.5.13 |
| I-AGENT-04 | `test_analyst_confidence_propagation` | 置信度传播 | — |

### 3.3 Graph 集成 (2 tests)

| ID | 测试名称 | 验证内容 | 依赖 |
|----|---------|---------|------|
| I-GRAPH-01 | `test_multi_chain_workflow_end_to_end` | 多链工作流 | T2.6.6 |
| I-GRAPH-02 | `test_trader_aggregates_all_reports` | Trader 聚合所有报告 | — |

---

## 4. E2E 测试 (3 tests)

### 4.1 场景测试

| ID | 测试名称 | 场景 | 预期结果 |
|----|---------|------|---------|
| E2E-01 | `test_btc_perp_analysis_full` | BTC-PERP 完整分析 | Analyst → Trader → Decision |
| E2E-02 | `test_eth_sol_macro_analysis` | ETH+SOL+Macro 分析 | 多链并行 → 汇总 |
| E2E-03 | `test_partial_chain_failure` | 单链失败场景 | 其他链正常，降级输出 |

---

## 5. Mock 策略

### 5.1 数据源 Mock

| 数据源 | Mock 方式 | 关键字段 |
|--------|----------|---------|
| CoinGecko | `responses` library | `data.market_data.current_price` |
| Binance Futures | `httpretty` / `responses` | `fundingRate`, `nextFundingTime` |
| Jupiter | `responses` | `data[0].price`, `data[0].change_24h` |
| GeckoTerminal | `responses` | `data.attributes.tvl_usd` |
| Alternative.me | `responses` | `data[0].value`, `data[0].value_classification` |
| Etherscan | `responses` | `result` |

### 5.2 Mock 数据文件

```
tests/fixtures/mock_data/
├── coingecko_eth.json
├── coingecko_btc_dominance.json
├── binance_funding_eth.json
├── jupiter_sol.json
├── geckoterminal_meme.json
├── fear_greed.json
└── etherscan_usdt.json
```

---

## 6. 测试环境

### 6.1 环境要求

- Python 3.11+
- 虚拟环境 (与 Phase 1 共享)
- 无需真实 API Key（全部 Mock）

### 6.2 测试命令

```bash
# 运行所有测试
cd /root/TradingAgents
python3 -m pytest tradingagents_crypto/tests/ -v

# 只运行单元测试
python3 -m pytest tradingagents_crypto/tests/unit/ -v

# 只运行集成测试
python3 -m pytest tradingagents_crypto/tests/integration/ -v

# 只运行 E2E 测试
python3 -m pytest tradingagents_crypto/tests/e2e/ -v

# 带覆盖率
python3 -m pytest --cov=tradingagents_crypto --cov-report=html
```

---

## 7. 验收标准

### 7.1 测试通过率

| 测试类型 | 目标 | 最低要求 |
|---------|------|---------|
| 单元测试 | 95% | 90% |
| 集成测试 | 90% | 85% |
| E2E 测试 | 100% | 100% |

### 7.2 功能验收

| 功能 | 测试覆盖 |
|------|---------|
| ETH 数据获取 | U-ETH-*, I-DATA-01 |
| SOL 数据获取 | U-SOL-*, I-DATA-02 |
| Macro 数据获取 | U-MACRO-*, I-DATA-03 |
| ETH Analyst | U-AGENT-ETH-*, I-AGENT-01 |
| SOL Analyst | U-AGENT-SOL-*, I-AGENT-02 |
| Macro Analyst | U-AGENT-MACRO-*, I-AGENT-03 |
| 多链并行 | U-GRAPH-01-05, I-GRAPH-01 |
| 多链汇总 | I-GRAPH-02, E2E-02 |
| 降级处理 | U-GRAPH-04, E2E-03 |

---

## 8. 测试统计

| 测试类型 | 数量 | 预计时间 |
|---------|------|---------|
| 单元测试 | 45 | 30s |
| 集成测试 | 12 | 60s |
| E2E 测试 | 3 | 90s |
| **总计** | **60** | **~3min** |

---

## 9. 修订历史

| 版本 | 日期 | 修订内容 |
|------|------|---------|
| v1.0 | 2026-04-01 | 初始版本 |
