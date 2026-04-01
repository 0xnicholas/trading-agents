# Phase 3 测试计划

**Phase**: M3.1 - M3.5
**前置条件**: Phase 1 + Phase 2 测试通过 ✅

---

## 测试策略

### 分层测试

| 层级 | 范围 | 网络依赖 | Mock策略 |
|------|------|---------|---------|
| Unit | 单个模块/函数 | ❌ 无 | ✅ 使用 mock 数据 |
| Integration | 多模块协作 | ⚠️ 最小化 | Mock API响应 |
| E2E | 完整回测案例 | ✅ 真实数据 | ❌ 不 mock |

### 通过标准

- **Unit**: 全部通过（0 failures）
- **Integration**: 全部通过（0 failures）
- **E2E**: Case 1-3 全部运行成功，输出有效 equity_curve

---

## M3.1 风控模块测试

### M3.1.1 LiquidationScenator

#### Unit Tests

| ID | 测试内容 | 输入 | 预期结果 |
|----|---------|------|---------|
| T_LIQ_01 | 20x多仓，价格下跌5%，Isolated Margin | entry=100, current=95, lev=20 | distance_to_liq ≈ 5%, recommendation="danger" |
| T_LIQ_02 | 5x多仓，安全垫充足 | entry=100, current=98, lev=5 | distance_to_liq > 10%, recommendation="safe" |
| T_LIQ_03 | 10x空仓，正常距离 | entry=100, current=105, lev=10 | recommendation="caution" 或 "safe" |
| T_LIQ_04 | 计算最大安全杠杆 | entry=100, current=95 | max_safe_leverage ≈ 19x |
| T_LIQ_05 | Cross Margin模式 | margin_mode="cross", lev=20 | 使用简化公式，不崩溃 |
| T_LIQ_06 | 边界：leverage=1 (无杠杆) | lev=1 | max_safe_leverage=1 |
| T_LIQ_07 | 边界：leverage=20 (最大) | lev=20 | 返回合理结果 |

**数学验证**:
```python
# Isolated Margin 多仓清算公式验证
# liq_price = entry_price * (1 - 1/leverage)
# distance_pct = (current - liq_price) / current * 100

# 20x, entry=100
# liq_price = 100 * (1 - 1/20) = 100 * 0.95 = 95
# current=95, distance_pct = (95-95)/95 * 100 = 0% ✓ danger

# 5x, entry=100, current=98
# liq_price = 100 * (1 - 1/5) = 100 * 0.8 = 80
# distance_pct = (98-80)/98 * 100 = 18.4% ✓ safe
```

#### 验收条件
- [ ] T_LIQ_01: "danger" 推荐
- [ ] T_LIQ_02: "safe" 推荐
- [ ] T_LIQ_04: max_safe_leverage ≈ 19 (误差 < 1)

---

### M3.1.2 HVAnalyst

#### Unit Tests

| ID | 测试内容 | 输入数据 | 预期结果 |
|----|---------|---------|---------|
| T_HV_01 | 低波动市场 | 30天HV=30%，ATR低 | recommended_leverage ≥ 8 |
| T_HV_02 | 高波动市场 | 30天HV=90%百分位 | recommended_leverage ≤ 3 |
| T_HV_03 | ATR计算正确 | 标准K线数据 | ATR值与手动计算误差<0.1% |
| T_HV_04 | HV百分位边界 | HV=0%, HV=100% | 不崩溃，返回合理百分位 |
| T_HV_05 | position="extreme"条件 | HV Percentile=95 | position="extreme" |
| T_HV_06 | 空数据/NaN处理 | 全NaN K线 | 返回默认值，不崩溃 |

**数学验证**:
```python
# HV = std(returns) * sqrt(365)
# returns = pct_change().dropna()

# 30天数据，假设日收益率std=0.02
# HV = 0.02 * sqrt(365) = 0.02 * 19.1 = 0.382 = 38.2%

# ATR验证
# 使用真实High-Low-Close数据
# 手动计算TR = max(H-L, |H-C_prev|, |L-C_prev|)
# ATR14 = SMA(TR, 14)
```

#### 验收条件
- [ ] T_HV_01: recommended_leverage ≥ 8
- [ ] T_HV_02: recommended_leverage ≤ 3
- [ ] T_HV_03: ATR误差 < 0.1%

---

### M3.1.3 ExposureMonitor

#### Unit Tests

| ID | 测试内容 | 场景 | 预期结果 |
|----|---------|------|---------|
| T_EXP_01 | 单币种超限 | BTC占比25% | violation包含"单币种上限" |
| T_EXP_02 | 单向暴露超限 | 同向仓位60% | violation包含"单向暴露" |
| T_EXP_03 | 全部规则通过 | 分散仓位 | approved=True, violations=[] |
| T_EXP_04 | 新仓位导致超限 | 已有仓位+新仓 | rejected |
| T_EXP_05 | 对冲仓位不超限 | 多+空BTC 50%净敞口 | 允许 |
| T_EXP_06 | 多币种分散警告 | 仅2个币种 | warning包含"分散度不足" |
| T_EXP_07 | 杠杆超限 | 某仓位lev=25 | violation包含"最大杠杆" |

**场景构建**:
```python
# T_EXP_01: 总权益$100,000
positions = [
    Position(symbol="BTC", side="long", size_usd=25000, ...),
]
# BTC占比25% > 20% → reject

# T_EXP_03: 分散良好
positions = [
    Position(symbol="BTC", side="long", size_usd=15000, ...),  # 15%
    Position(symbol="ETH", side="long", size_usd=15000, ...),  # 15%
    Position(symbol="SOL", side="long", size_usd=10000, ...),  # 10%
]
# 全部 < 20%, 同向 < 60% → approved
```

#### 验收条件
- [ ] T_EXP_01: BTC占比25%被reject
- [ ] T_EXP_02: 同向60%被reject
- [ ] T_EXP_05: 对冲仓位不触发违规

---

### M3.1.4 LiquidityChecker

#### Unit Tests

| ID | 测试内容 | 输入 | 预期结果 |
|----|---------|------|---------|
| T_LIQCHK_01 | 低滑点 | size=1000, depth=100000 | slippage < 5 bps |
| T_LIQCHK_02 | 高滑点 | size=50000, depth=100000 | slippage > 20 bps |
| T_LIQCHK_03 | 滑点上限 | size=1000000, depth=1000 | slippage ≤ 50 bps |
| T_LIQCHK_04 | Long vs Short | 同size不同side | 滑点不同（depth不同）|
| T_LIQCHK_05 | 零depth | depth=0 | 不崩溃，返回50 bps |

**数学验证**:
```python
# slippage_bps = min(ratio ** 0.7 * 10, 50)

# T_LIQCHK_01: ratio = 1000/100000 = 0.01
# slippage = min(0.01 ** 0.7 * 10, 50) = min(0.25, 50) = 0.25 bps ✓

# T_LIQCHK_02: ratio = 50000/100000 = 0.5
# slippage = min(0.5 ** 0.7 * 10, 50) = min(3.76, 50) = 3.76 bps
# (实际需要更大ratio才能触发>20)

# T_LIQCHK_03: ratio = 1000000/1000 = 1000
# slippage = min(1000 ** 0.7 * 10, 50) = min(158, 50) = 50 bps ✓
```

#### 验收条件
- [ ] T_LIQCHK_03: 滑点不超过50 bps上限

---

### M3.1.5 CryptoPortfolioManager

#### Unit Tests

| ID | 测试内容 | 场景 | 预期结果 |
|----|---------|------|---------|
| T_PM_01 | 添加多仓 | new_position=long | 返回True，持仓增加 |
| T_PM_02 | 添加空仓 | new_position=short | 返回True，持仓增加 |
| T_PM_03 | 移除仓位 | remove_position("BTC") | 返回仓位对象 |
| T_PM_04 | 总权益计算 | 多空混合 | equity = sum(mark_value) |
| T_PM_05 | 暴露度计算 | 3个仓位 | exposure正确汇总 |
| T_PM_06 | 工厂函数crypto | config["mode"]="crypto" | 返回CryptoPortfolioManager |
| T_PM_07 | 工厂函数stock | config["mode"]="stock" | 返回StockPortfolioManager |

#### 验收条件
- [ ] T_PM_06: 工厂函数正确路由

---

## M3.2 回测引擎测试

### M3.2.1 BacktestEngine

#### Unit Tests

| ID | 测试内容 | 输入 | 预期结果 |
|----|---------|------|---------|
| T_BT_01 | 简单趋势策略 | MA金叉/死叉 | 有交易记录 |
| T_BT_02 | equity_curve单调增 | 持续做多 | equity随价格变化 |
| T_BT_03 | 手续费扣除 | 高频交易 | 手续费从equity扣除 |
| T_BT_04 | 无信号时hold | 无交叉 | 无新交易 |
| T_BT_05 | 多symbol支持 | BTC+ETH | 各自独立equity |
| T_BT_06 | 边界：空数据 | start>end | 抛出异常 |

#### Integration Tests

| ID | 测试内容 | 场景 | 预期结果 |
|----|---------|------|---------|
| T_BT_INT_01 | Case 1完整运行 | MA策略1年 | equity_curve长度>0 |
| T_BT_INT_02 | 数据缺口处理 | 5%缺失数据 | completeness警告 |

#### 验收条件
- [ ] T_BT_01: 交易记录数 > 0
- [ ] T_BT_03: 手续费被扣除
- [ ] T_BT_INT_01: Case 1 运行完成

---

### M3.2.2 FundingSimulator

#### Unit Tests

| ID | 测试内容 | 输入 | 预期结果 |
|----|---------|------|---------|
| T_FUND_01 | 正费率-多仓 | rate=0.0001, long | pnl < 0 (多仓付钱) |
| T_FUND_02 | 正费率-空仓 | rate=0.0001, short | pnl > 0 (空仓收钱) |
| T_FUND_03 | 负费率-多仓 | rate=-0.0001, long | pnl > 0 (多仓收钱) |
| T_FUND_04 | 负费率-空仓 | rate=-0.0001, short | pnl < 0 (空仓付钱) |
| T_FUND_05 | 零费率 | rate=0 | pnl=0 |
| T_FUND_06 | 方向验证 | 4种组合 | 符号正确 |

**数学验证**:
```python
# 正费率 (rate > 0)
# 多仓: pnl = -rate * value = -0.0001 * 10000 = -1
# 空仓: pnl = rate * value = 0.0001 * 10000 = +1

# 负费率 (rate < 0)
# 多仓: pnl = -(-0.0001) * 10000 = +1
# 空仓: pnl = -0.0001 * 10000 = -1
```

#### 验收条件
- [ ] T_FUND_01: 多仓亏损
- [ ] T_FUND_02: 空仓盈利
- [ ] T_FUND_03: 负费率多仓盈利

---

### M3.2.3 SlippageEstimator

#### Unit Tests

| ID | 测试内容 | 输入 | 预期结果 |
|----|---------|------|---------|
| T_SLIP_01 | 基准计算 | size/depth比例已知 | 滑点值符合公式 |
| T_SLIP_02 | 非线性验证 | 多个比例点 | 公式非线性特性 |
| T_SLIP_03 | 上限50bps | 极大size | slippage ≤ 50 |

#### 验收条件
- [ ] T_SLIP_03: 上限50bps不被突破

---

### M3.2.4 Benchmark

#### Unit Tests

| ID | 测试内容 | 数据 | 预期结果 |
|----|---------|------|---------|
| T_BM_01 | 夏普比率计算 | 已知收益序列 | 与手动计算误差<0.01 |
| T_BM_02 | 最大回撤 | 已知equity | 回撤值正确 |
| T_BM_03 | 卡玛比率 | 已知equity | ratio = annual_return / max_dd |
| T_BM_04 | 胜率计算 | 已知trades | win_rate正确 |

#### 验收条件
- [ ] T_BM_01: 夏普比率误差 < 0.01

---

## M3.3 回测数据层测试

| ID | 测试内容 | 预期结果 |
|----|---------|---------|
| T_CACHE_01 | Parquet读写 | 数据一致 |
| T_CACHE_02 | 数据缺口检测 | 返回正确缺口数 |
| T_CACHE_03 | K线合并 | 无重复时间戳 |

---

## M3.4 回测案例测试 (E2E)

### Case 1: MA趋势跟踪策略

| 步骤 | 测试内容 | 验收条件 |
|------|---------|---------|
| 1 | 加载1年BTC-PERP数据 | 数据完整 |
| 2 | 运行MA金叉/死叉策略 | 交易数 > 0 |
| 3 | 计算equity_curve | 序列长度 = K线条数 |
| 4 | 资金费率扣除 | 包含负向调整 |
| 5 | 生成报告 | Markdown文件生成 |

### Case 2: 资金费率均值回归策略

| 步骤 | 测试内容 | 验收条件 |
|------|---------|---------|
| 1 | 加载历史资金费率 | funding_rate序列有效 |
| 2 | 运行策略 | 有做空/做多信号 |
| 3 | 72h强制平仓 | 持仓时间不超72h |

### Case 3: 跨链动量策略

| 步骤 | 测试内容 | 验收条件 |
|------|---------|---------|
| 1 | BTC-PERP + SOL-PERP数据 | 数据并行可用 |
| 2 | BTC涨幅>2%触发SOL信号 | 规则正确执行 |
| 3 | -5%止损 | 亏损交易有止损记录 |

---

## 测试数据构建

### 合成K线数据（无网络依赖）

```python
def generate_synthetic_candles(
    days: int = 365,
    interval: str = "1h",
    start_price: float = 100,
    volatility: float = 0.02,
) -> pd.DataFrame:
    """
    生成合成K线数据用于单元测试。

    - 几何布朗运动模拟
    - 趋势+噪声
    - 无网络依赖
    """
    n_bars = days * 24 if interval == "1h" else days
    dt = 1 / (24 * 365)
    drift = 0.0
    diffusion = volatility * np.sqrt(dt)

    returns = np.random.normal(drift * dt, diffusion, n_bars)
    price = start_price * np.exp(np.cumsum(returns))

    # 构建OHLCV
    # ... (生成高/低/开/收/量)
```

### 合成资金费率数据

```python
def generate_synthetic_funding(
    days: int = 365,
    base_rate: float = 0.0001,
) -> pd.DataFrame:
    """每8h一个费率记录，随机正负波动"""
```

---

## 测试环境要求

- **无网络模式**: 所有测试可在无外网环境下运行
- **数据Mock**: 使用合成数据，不依赖真实API
- **随机种子**: `np.random.seed(42)` 确保可复现

---

## 测试覆盖目标

| 指标 | 目标 |
|------|------|
| 行覆盖率 | ≥ 85% |
| 分支覆盖率 | ≥ 75% |
| 单元测试数 | ≥ 50 |
| 集成测试数 | ≥ 5 |
| E2E案例 | 3 (Case 1/2/3) |

---

## 测试执行

```bash
# 运行所有测试
cd /root/TradingAgents
python3 -m pytest tradingagents_crypto/tests/unit/test_liquidation_scenator.py -v
python3 -m pytest tradingagents_crypto/tests/unit/test_hv_analyst.py -v
python3 -m pytest tradingagents_crypto/tests/unit/test_exposure_monitor.py -v
python3 -m pytest tradingagents_crypto/tests/unit/test_liquidity_checker.py -v
python3 -m pytest tradingagents_crypto/tests/unit/test_funding_simulator.py -v
python3 -m pytest tradingagents_crypto/tests/unit/test_slippage_estimator.py -v
python3 -m pytest tradingagents_crypto/tests/unit/test_benchmark.py -v
python3 -m pytest tradingagents_crypto/tests/unit/test_backtest_engine.py -v

# 运行集成测试
python3 -m pytest tradingagents_crypto/tests/integration/ -v

# 运行E2E案例
python3 -m pytest tradingagents_crypto/tests/integration/test_case1_ma_strategy.py -v
python3 -m pytest tradingagents_crypto/tests/integration/test_case2_funding_strategy.py -v
python3 -m pytest tradingagents_crypto/tests/integration/test_case3_cross_chain.py -v
```

---

## 修订历史

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-04-02 | v1.0 | 初始版本 |
