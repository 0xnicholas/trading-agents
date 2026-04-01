# Phase 3：风控 + 回测框架

**周期**: 2-3 周
**前置条件**: Phase 1 + Phase 2 完成并通过验收
**目标**: 构建 Crypto 专属风险管理体系 + 规则化策略回测框架

**架构决策**：回测引擎采用**路径 A**（规则化信号回测），而非 LLM Agent 决策重放。Agent 负责生成规则策略，回测引擎验证规则的历史表现。

---

## 里程碑

### M3.0：数据范围验证（Day 1）

与 M1.0/M2.0 并行，验证回测所需历史数据范围：

- [ ] `candles_snapshot()` — 查询 BTC-PERP K 线最早可用日期
- [ ] `funding_history()` — 查询资金费率最早可用日期
- [ ] Binance `/fapi/v1/fundingRate` — 历史数据最早日期
- [ ] 输出：`docs/backtest_data_range.md`

**回测起始日期**将根据实际上线时间调整（而非 2024-01-01）。

---

### M3.1：Risk Manager Agent（Day 2-7）

#### M3.1.1 LiquidationScenator
- [ ] `agents/risk_mgmt/liquidation_scenator.py`
  - 使用 Hyperliquid 官方清算公式
  - **公式**：`liquidation_price(做多) = entry_price × (1 - 1 / leverage)`
  - **安全垫**：`distance_pct = (current_price - liq_price) / current_price × 100%`
  - 输入：direction / entry_px / current_px / leverage
  - 输出：
    ```python
    {
        "liquidation_price": float,
        "distance_to_liq_pct": float,   # 安全垫 %
        "recommendation": "safe (>10%) | caution (5-10%) | danger (<5%)",
        "max_safe_leverage_for_entry": float
    }
    ```

#### M3.1.2 HVAnalyst（历史波动率）
- [ ] `agents/risk_mgmt/hv_analyst.py`（原 VolAnalyst，移除 IV）
  - 计算 30 天历史波动率（年化）
  - 计算 HV Percentile（当前 HV 在过去 30 天中的位置）
  - ATR 计算（14 周期）
  - 输出：
    ```python
    {
        "hv_annualized": 0.65,
        "hv_percentile_30d": 85,
        "atr_14": 500.0,
        "atr_pct": 0.0075,
        "position": "low (<30%) | medium | high (>70%) | extreme (>90%)",
        "recommended_leverage": 5,  # 根据波动率调整
        "verdict": "降低仓位 | 正常 | 可适当加仓"
    }
    ```
  - **注**：不依赖 IV 数据（Hyperliquid 无期权数据）

#### M3.1.3 ExposureMonitor
- [ ] `agents/risk_mgmt/exposure_monitor.py`
  - 单币种仓位上限：20% 总权益
  - 单向总暴露上限：60% 总权益
  - 最大杠杆：20x
  - 多币种分散度检查（>=3 币种）
  - 输出：
    ```python
    {
        "violations": [
            {"rule": "单币种上限", "detail": "BTC-PERP 占比 25%", "action": "reject"}
        ],
        "warnings": [...],
        "approved": bool
    }
    ```

#### M3.1.4 LiquidityChecker
- [ ] `agents/risk_mgmt/liquidity_checker.py`
  - 滑点估算公式（**非历史数据**，为假设模型）：
    ```
    滑点(bps) = min(position_size_usd / avg_book_depth_usd × 10, 50)
    ```
  - 基于当前订单簿深度计算
  - 输出：
    ```python
    {
        "estimated_slippage_bps": 3.5,
        "liquidity_risk": "low | medium | high",
        "recommendation": "正常开仓 | 降低仓位 | 拒绝"
    }
    ```

#### M3.1.5 CryptoPortfolioManager（新增）
- [ ] `agents/managers/crypto_portfolio_manager.py`（**不修改原 portfolio_manager.py**）
  - 支持做空仓位表示
  - 保证金率检查
  - 多币种混合持仓计算
  - 与 `StockPortfolioManager` 完全独立
  - 通过 `config["mode"]` 路由：
    ```python
    if config["mode"] == "crypto":
        pm = CryptoPortfolioManager(config)
    else:
        pm = StockPortfolioManager(config)
    ```

---

### M3.2：回测引擎（Day 8-14）

#### M3.2.1 核心引擎
- [ ] `backtest/backtest_engine.py`
  - **时间基准**：按小时（而非交易日），支持 24/7 市场
  - **信号接口**（规则化，非 LLM）：
    ```python
    def strategy_signal(
        timestamp: int,
        candles: dict[str, pd.DataFrame],   # {interval: df}
        funding: float,
        oi: float,
        indicators: dict
    ) -> TradeSignal | None:
        """用户定义的规则化策略函数"""
        ...
    ```
  - **回测流程**：
    1. 遍历 `start_date` → `end_date` 每个时间点
    2. 调用 `strategy_signal()` 获取信号
    3. 模拟订单执行（市价单）
    4. 计入手续费 + 滑点 + 资金费率
    5. 更新权益
  - **运行接口**：
    ```python
    result = engine.run(
        strategy_fn=strategy_signal,
        start_date="2024-06-01",   # 根据实际上线时间调整
        end_date="2026-03-31",
        symbols=["BTC", "ETH"],
        initial_capital=100_000,
        commission_rate=0.0004,
        slippage_bps=5.0,
    )
    ```

#### M3.2.2 资金费率模拟器
- [ ] `backtest/funding_simulator.py`
  - 加载历史资金费率（`funding_history()` 获取）
  - 每个结算周期（8h）计算：
    - 多仓：支付 funding_rate × position_value
    - 空仓：收取 funding_rate × position_value
  - 累计资金费率 PnL

#### M3.2.3 滑点模型（假设估算）
- [ ] `backtest/slippage_estimator.py`
  - **不依赖历史订单簿**，使用估算公式：
    ```python
    def estimate_slippage(
        position_size_usd: float,
        bid_depth_usd: float,    # 订单簿 bid 侧总深度
        ask_depth_usd: float,    # 订单簿 ask 侧总深度
        side: str,               # "long" 或 "short"
    ) -> float:
        """返回滑点估算（bps）"""
        depth = bid_depth_usd if side == "long" else ask_depth_usd
        ratio = position_size_usd / depth
        # 非线性模型：滑点 = ratio^0.7 × 10，上限 50 bps
        slippage = min(ratio ** 0.7 * 10, 50)
        return slippage
    ```
  - 参数基于合理假设，标注为估算值

#### M3.2.4 基准比较器
- [ ] `backtest/benchmark.py`
  - vs Buy & Hold（买入持有）
  - vs 单币种持有（BTC、ETH）
  - 计算：夏普比率 / 最大回撤 / 卡玛比率 / 胜率 / 盈亏比

---

### M3.3：回测数据层（Day 6-10，并行于 M3.2）

- [ ] 历史 K 线缓存扩展
  - 扩展 Phase 1 的 SQLite 缓存，覆盖完整回测时间窗口
  - 存储格式：`{symbol}_{interval}_{start}_{end}.parquet`（改为 Parquet 提升性能）

- [ ] 历史资金费率缓存
  - 每日凌晨补充最新资金费率数据
  - 缓存 TTL：1 小时

- [ ] 数据完整性检查
  - 检测并填补缺失的 K 线数据
  - 记录数据缺口（用于回测结果中标注置信度）

---

### M3.4：规则化回测案例（Day 15-18）

**重要**：以下案例的策略都是**规则化的**（MA 交叉、资金费率阈值等），非 LLM 决策。

#### Case 1：MA 趋势跟踪策略
```
规则：
  - 1h MA50 > MA200 → 做多
  - 1h MA50 < MA200 → 做空
  - 资金费率 > 0.05%（年化 > 15%）→ 禁止开空仓
  - OI 膨胀 > 20% → 降低仓位 50%
参数：
  - 标的：BTC-PERP
  - 初始资金：$100,000
  - 杠杆：5x（根据 HV 动态调整 3-10x）
  - 手续费：0.04%
  - 滑点：5 bps（估算）
```

#### Case 2：资金费率均值回归策略
```
规则：
  - 8h 资金费率 > 0.01% → 做空（过度投机会）
  - 8h 资金费率 < -0.01% → 做多（套利机会）
  - OI 趋势确认：OI 收缩时优先做多资金费率
  - 最大持仓时间：72h（强制平仓）
参数：同上
```

#### Case 3：BTC-PERP × SOL-DEX 现货跨链动量
```
规则（Phase 2 后可用）：
  - BTC-PERP 1h 涨幅 > 2% → 下一小时做多 SOL 现货
  - SOL DEX 流动性 < $100k → 跳过信号
  - Hyperliquid OI 膨胀 > 15% → 减半仓
  - SOL 现货止损：-5%
参数：同上
```

---

### M3.5：报告系统（Day 19-21）

#### 可视化
- [ ] `backtest/reporting.py`
  - 资金曲线（equity_curve）
  - 回撤曲线（drawdown_curve）
  - 月度收益热力图
  - 交易日志表

#### 报告生成
- [ ] Markdown 报告（优先）
  - 关键指标汇总
  - 资金曲线图（Base64 嵌入）
  - trade_log 摘要
  - 数据完整性说明（缺失数据比例）
- [ ] PDF 报告（可选，`reportlab`）

---

## 回测数据范围（待验证）

以下为初步估计，需 M3.0 验证后调整：

| 数据 | 预期可用范围 | 来源 |
|------|------------|------|
| BTC-PERP K 线 | ~2024-06 起（HL 主网上线） | `candles_snapshot` |
| ETH-PERP K 线 | ~2024-06 起 | `candles_snapshot` |
| SOL-PERP K 线 | ~2024-09 起 | `candles_snapshot` |
| Hyperliquid 资金费率 | ~2024-06 起 | `funding_history` |
| Binance ETH-PERP 费率 | ~2020 起（ Binance 早已上线） | Binance Futures API |

---

## 置信度标注（回测结果）

回测结果必须标注数据质量和模型假设：

```python
@dataclass
class BacktestConfidence:
    data_completeness: float       # K 线缺失比例（如 0.95 = 5% 缺失）
    slippage_model: str            # "estimated"（假设，非真实历史）
    funding_history: str           # "real" | "partial"
    leverage_effects: str         # "simplified"（未考虑保证金复杂计算）
```

---

## 验收标准

### 风控验收

| 功能 | 验收条件 |
|------|---------|
| 清算模拟 | 20x 多仓，价格下跌 5% → 距离清算 < 5% → "danger" |
| HV 分析 | HV 90% 分位时 `recommended_leverage` ≤ 3 |
| 敞口监控 | 4 个同向仓位占总权益 60% → 第 5 个被 reject |
| 滑点估算 | 公式存在，不崩溃 |
| Portfolio Manager | `config["mode"]` 路由正确 |

### 回测验收

| 功能 | 验收条件 |
|------|---------|
| 回测引擎 | Case 1 运行完成，输出正确 equity_curve |
| 资金费率成本 | 与手动计算误差 < 1% |
| 滑点估算 | 公式可调用，不依赖外部历史数据 |
| 指标计算 | 夏普 / 最大回撤 / 胜率 与 `empiricist` 或手动计算一致 |
| 数据完整性 | K 线缺失 > 5% 时报告警告 |
| 极端行情 | 数据按时间戳过滤，无未来数据泄露 |

---

## 修订说明（相比初版）

| # | 问题 | 修订 |
|---|------|------|
| 1 | 回测起始日期错误 | ✅ 改为 2024-06（需 M3.0 确认），已加 M3.0 验证 |
| 2 | Case 3 SOL-PERP 冲突 | ✅ 改为 BTC-PERP × SOL-DEX 现货 |
| 3 | 无法回测 LLM Agent | ✅ 明确路径 A：规则化信号回测，Agent 生成规则 |
| 4 | Portfolio Manager 冲突 | ✅ 新增 `crypto_portfolio_manager.py`，不修改原文件 |
| 5 | 资金费率历史范围未验证 | ✅ M3.0 增加验证 |
| 6 | IV 数据不存在 | ✅ 改 HVAnalyst（移除 IV），标注 IV 为 Phase 3.5 |
| 7 | 维持保证金假设简化 | ✅ 使用 Hyperliquid 官方公式 |
| 8 | 历史订单簿不存在 | ✅ 改为假设估算公式，不依赖历史数据 |
| 9 | M3.1/M3.2 时间重叠 | ✅ M3.2 改为 Day 8-14，M3.3 并行 |
| 10 | 回测时间窗口不一致 | ✅ 与 HL 实际上线时间对齐 |
| 11 | 多币种保证金计算 | ✅ 简化假设，标注局限性 |
| 12 | PDF 报告 | ✅ 明确 MD 优先，PDF 可选 |

---

*Phase 3 完成后，项目具备完整的多链分析 + 风控 + 回测能力，可作为独立的研究和策略验证工具。*
