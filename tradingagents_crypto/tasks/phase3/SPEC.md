# Phase 3：风控 + 回测框架

**状态**: 🔵 待启动
**周期**: 2-3 周
**前置条件**: Phase 1 + Phase 2 完成 ✅

---

## 目标

构建 Crypto 专属风险管理体系 + 规则化策略回测引擎。

**架构决策**：
- 回测引擎采用**路径 A**（规则化信号回测），而非 LLM Agent 决策重放
- Agent 负责生成规则策略，回测引擎验证规则的历史表现
- OI（Open Interest）数据源需 M3.0 验证可用性

---

## 核心模块设计

### 1. Risk Manager Agent

#### 1.1 LiquidationScenator
**文件**: `agents/risk_mgmt/liquidation_scenator.py`

```python
@dataclass
class LiquidationResult:
    liquidation_price: float          # 清算价格
    distance_to_liq_pct: float       # 安全垫 %
    recommendation: str               # "safe" | "caution" | "danger"
    max_safe_leverage: float         # 当前价格下安全最大杠杆

def calc_liquidation(
    direction: Literal["long", "short"],
    entry_price: float,
    current_price: float,
    leverage: float,
    margin_mode: Literal["isolated", "cross"] = "isolated",
) -> LiquidationResult:
    """
    计算清算价格和安全垫。

    Isolated Margin:
        long: liq_price = entry_price * (1 - 1 / leverage)
        short: liq_price = entry_price * (1 + 1 / leverage)

    Cross Margin:
        简化: liq_price ≈ entry_price * (1 - 1 / (leverage * mm_ratio))
        mm_ratio ≈ 0.005 (0.5% maintenance margin)
    """
```

**安全垫阈值**:
- `> 10%` → "safe"
- `5-10%` → "caution"
- `< 5%` → "danger"

#### 1.2 HVAnalyst
**文件**: `agents/risk_mgmt/hv_analyst.py`

```python
@dataclass
class HVAnalysis:
    hv_annualized: float      # 30天年化波动率
    hv_percentile_30d: int    # HV在过去30天中的百分位 (0-100)
    atr_14: float             # ATR (14周期)
    atr_pct: float            # ATR占价格百分比
    position: str              # "low" | "medium" | "high" | "extreme"
    recommended_leverage: int  # 根据波动率推荐杠杆
    verdict: str               # 交易建议

def analyze_hv(candles_1h: pd.DataFrame) -> HVAnalysis:
    """
    计算历史波动率和ATR。

    HV计算:
        returns = candles["close"].pct_change().dropna()
        hv = returns.std() * sqrt(365)  # 年化

    ATR计算:
        high_low = candles["high"] - candles["low"]
        high_close = abs(candles["high"] - candles["close"].shift())
        low_close = abs(candles["low"] - candles["close"].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
    """
```

**杠杆推荐表**:
| HV Percentile | 推荐杠杆 |
|--------------|---------|
| < 30% (低波动) | 8-10x |
| 30-70% (正常) | 5-7x |
| 70-90% (高波动) | 3-4x |
| > 90% (极端) | 1-2x |

#### 1.3 ExposureMonitor
**文件**: `agents/risk_mgmt/exposure_monitor.py`

```python
@dataclass
class ExposureCheckResult:
    violations: list[dict]    # 违规列表
    warnings: list[dict]      # 警告列表
    approved: bool            # 是否批准开仓

@dataclass
class Position:
    symbol: str
    side: Literal["long", "short"]
    size_usd: float           # 仓位美元价值
    entry_price: float
    current_price: float

def check_exposure(
    positions: list[Position],
    total_equity: float,
    new_position: Position | None = None,
) -> ExposureCheckResult:
    """
    检查敞口限制。

    规则:
    - 单币种仓位上限: 20% 总权益
    - 单向总暴露上限: 60% 总权益
    - 最大杠杆: 20x
    - 多币种分散度: >= 3 币种 (警告)

    注意: 空仓和多仓可以同时存在（对冲），但净敞口不能超限
    """
```

#### 1.4 LiquidityChecker
**文件**: `agents/risk_mgmt/liquidity_checker.py`

```python
@dataclass
class LiquidityCheckResult:
    estimated_slippage_bps: float  # 估算滑点 (bps)
    liquidity_risk: str            # "low" | "medium" | "high"
    recommendation: str            # "正常开仓" | "降低仓位" | "拒绝"

def estimate_slippage(
    position_size_usd: float,
    bid_depth_usd: float,
    ask_depth_usd: float,
    side: Literal["long", "short"],
) -> float:
    """
    估算滑点 (非历史数据，基于假设模型)。

    公式:
        depth = bid_depth if side == "long" else ask_depth
        ratio = position_size_usd / depth
        slippage_bps = min(ratio ** 0.7 * 10, 50)  # 非线性模型，上限50bps

    阈值:
    - < 5 bps: "low"
    - 5-20 bps: "medium"
    - > 20 bps: "high"
    """
```

#### 1.5 CryptoPortfolioManager
**文件**: `agents/managers/crypto_portfolio_manager.py`

```python
@dataclass
class CryptoPosition:
    symbol: str
    side: Literal["long", "short"]
    size: float              # 合约数量
    entry_price: float
    mark_price: float
    leverage: int
    margin_usd: float       # 保证金美元价值
    unrealized_pnl: float
    realized_pnl: float

class CryptoPortfolioManager:
    """
    Crypto专属投资组合管理器。

    与 StockPortfolioManager 完全独立，通过工厂函数创建:
        from agents.managers import create_portfolio_manager
        pm = create_portfolio_manager(config)

    功能:
    - 支持做空仓位
    - 保证金率检查
    - 多币种混合持仓
    - 账户权益计算 (mark_price based)
    """

    def add_position(self, position: CryptoPosition) -> bool:
        """添加仓位，返回是否成功（失败时抛出ExposureViolation）"""

    def remove_position(self, symbol: str) -> CryptoPosition | None:

    def get_total_equity(self) -> float:

    def get_total_exposure(self) -> dict[str, float]:  # {symbol: usd_value}

    def check_liquidation(self) -> list[CryptoPosition]:  # 返回接近清算的仓位
```

**工厂函数** (`agents/managers/__init__.py`):
```python
def create_portfolio_manager(config: dict) -> PortfolioManager:
    """根据 config['mode'] 创建对应 PM。"""
    if config.get("mode") == "crypto":
        return CryptoPortfolioManager(config)
    return StockPortfolioManager(config)
```

---

### 2. 回测引擎

#### 2.1 核心引擎
**文件**: `backtest/backtest_engine.py`

```python
@dataclass
class TradeSignal:
    action: Literal["open_long", "open_short", "close", "reduce", "hold"]
    size_pct: float = 1.0    # 仓位比例 (0.0-1.0)
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None

@dataclass
class BacktestResult:
    equity_curve: pd.Series          # 时间序列权益
    trades: list[dict]              # 交易日志
    metrics: dict                   # 性能指标
    confidence: BacktestConfidence  # 数据质量标注

def run_backtest(
    strategy_fn: Callable,           # 策略信号函数
    start_date: str,                # "2024-06-01"
    end_date: str,                  # "2026-03-31"
    symbols: list[str],
    interval: str = "1h",          # K线周期
    initial_capital: float = 100_000,
    commission_rate: float = 0.0004, # 单向手续费率
    slippage_bps: float = 5.0,
) -> BacktestResult:
    """
    运行回测。

    流程:
    1. 加载历史K线数据
    2. 按interval遍历每个时间点
    3. 调用 strategy_fn(timestamp, candles, funding, oi, indicators)
    4. 模拟订单执行 (市价单)
    5. 计算手续费 + 滑点 + 资金费率
    6. 更新权益

    注意:
    - 按K线条数遍历，非wall-clock时间
    - 1年回测 ≈ 8,760条1h K线
    - funding按实际历史数据时间点应用，非固定8h
    """
```

#### 2.2 资金费率模拟器
**文件**: `backtest/funding_simulator.py`

```python
def calc_funding_pnl(
    position_side: Literal["long", "short"],
    position_value: float,
    funding_rate: float,
) -> float:
    """
    计算资金费PnL。

    规则:
    - funding_rate > 0 (正费率): 多仓付钱给空仓
        long: pnl = -funding_rate * position_value
        short: pnl = funding_rate * position_value
    - funding_rate < 0 (负费率): 空仓付钱给多仓
        long: pnl = -funding_rate * position_value  # 负负得正
        short: pnl = funding_rate * position_value  # 负正得负
    """
```

#### 2.3 滑点估算器
**文件**: `backtest/slippage_estimator.py`

```python
def estimate_slippage(
    position_size_usd: float,
    bid_depth_usd: float,
    ask_depth_usd: float,
    side: Literal["long", "short"],
) -> float:
    """
    估算滑点 (bps)。

    非线性模型:
        depth = bid_depth if long else ask_depth
        ratio = position_size_usd / depth
        slippage = min(ratio ** 0.7 * 10, 50)

    标注: 此为假设估算，非历史订单簿数据
    """
```

#### 2.4 基准比较器
**文件**: `backtest/benchmark.py`

```python
@dataclass
class BenchmarkMetrics:
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float          # 年化收益 / 最大回撤
    win_rate: float
    profit_factor: float         # 盈利总额 / 亏损总额
    avg_trade_duration_hours: float
    total_trades: int

def compare_benchmark(
    backtest_result: BacktestResult,
    benchmark_symbols: list[str] = ["BTC", "ETH"],
) -> dict[str, BenchmarkMetrics]:
    """
    与Buy&Hold基准比较。
    """
```

#### 2.5 报告生成器
**文件**: `backtest/reporting.py`

```python
def generate_markdown_report(
    result: BacktestResult,
    strategy_name: str,
    output_path: str,
) -> str:
    """
    生成Markdown回测报告。

    内容:
    - 关键指标汇总表
    - 资金曲线 (Base64)
    - 回撤曲线 (Base64)
    - 月度收益热力图
    - trade_log摘要
    - 数据完整性说明
    - 置信度标注
    """
```

---

### 3. 回测数据层

#### 3.1 历史K线缓存
**文件**: `backtest/data_cache.py`

```python
class BacktestDataCache:
    """
    历史K线缓存管理器。

    存储格式: Parquet (提升性能)
    文件命名: {symbol}_{interval}_{start}_{end}.parquet
    """

    def get_candles(
        self,
        symbol: str,
        interval: str,
        start: str,
        end: str,
    ) -> pd.DataFrame:
        """
        获取历史K线。

        优先从本地Parquet读取
        → 其次从API获取并缓存
        → 返回合并后的数据
        """

    def get_funding_history(
        self,
        symbol: str,
        start: str,
        end: str,
    ) -> pd.DataFrame:
        """获取历史资金费率。"""

    def check_gaps(self, df: pd.DataFrame) -> dict:
        """
        检测K线数据缺口。

        返回:
            {
                "total_gaps": int,
                "total_missing_bars": int,
                "gaps": list[(start, end, missing_count)],
                "completeness": float  # 0.0-1.0
            }
        """
```

---

## 目录结构

```
tradingagents_crypto/
├── agents/
│   ├── risk_mgmt/
│   │   ├── __init__.py
│   │   ├── liquidation_scenator.py   # M3.1.1
│   │   ├── hv_analyst.py              # M3.1.2
│   │   ├── exposure_monitor.py        # M3.1.3
│   │   └── liquidity_checker.py       # M3.1.4
│   └── managers/
│       ├── __init__.py                # 工厂函数
│       └── crypto_portfolio_manager.py # M3.1.5
├── backtest/
│   ├── __init__.py
│   ├── backtest_engine.py             # M3.2.1
│   ├── funding_simulator.py           # M3.2.2
│   ├── slippage_estimator.py          # M3.2.3
│   ├── benchmark.py                   # M3.2.4
│   ├── reporting.py                   # M3.5
│   └── data_cache.py                  # M3.3
└── tests/
    ├── unit/
    │   ├── test_liquidation_scenator.py
    │   ├── test_hv_analyst.py
    │   ├── test_exposure_monitor.py
    │   ├── test_liquidity_checker.py
    │   ├── test_funding_simulator.py
    │   ├── test_slippage_estimator.py
    │   ├── test_benchmark.py
    │   └── test_backtest_engine.py
    └── integration/
        ├── test_case1_ma_strategy.py   # M3.4 Case 1
        ├── test_case2_funding_strategy.py  # M3.4 Case 2
        └── test_case3_cross_chain.py  # M3.4 Case 3
```

---

## 数据依赖

| 模块 | 数据来源 | 备注 |
|------|---------|------|
| HVAnalyst | 1h K线 | 从HL API获取 |
| LiquidationScenator | 当前价格 | 实时数据 |
| ExposureMonitor | 账户持仓 | 实时数据 |
| LiquidityChecker | 订单簿深度 | 实时数据 |
| BacktestEngine | 历史K线 + 资金费率 | 本地缓存/Parquet |
| FundingSimulator | 历史资金费率 | 从HL API获取 |

---

## 置信度标注

```python
@dataclass
class BacktestConfidence:
    data_completeness: float    # K线缺失比例 (0.95 = 5%缺失)
    slippage_model: str         # "estimated" | "historical"
    funding_history: str        # "real" | "partial"
    leverage_effects: str      # "simplified" | "full"
```

回测报告必须包含 `BacktestConfidence`，用于判断结果可信度。

---

## 修订历史

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-04-02 | v1.0 | 初始版本 |
