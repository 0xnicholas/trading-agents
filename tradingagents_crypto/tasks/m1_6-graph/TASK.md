# M1.6：Graph 集成

**状态**: 🔵 就绪（未开始）
**周期**: Day 11-15
**前置依赖**: M1.5 ✅（Agent 层）

---

## 任务目标

实现 `CryptoTradingAgentsGraph`，复用原 TradingAgents 的 `setup.py` / `propagation.py` / `reflection.py` 模块，替换数据层和 Analyst，实现端到端 `propagate()` 流程。

---

## 详细子任务

### T1.6.1 `graph/crypto_trading_graph.py` — 主 Graph 类
- [ ] 创建 `CryptoTradingAgentsGraph` 类
  ```python
  class CryptoTradingAgentsGraph:
      def __init__(self, config: dict):
          self.config = config
          self.data = HyperliquidDataBridge(config)  # 数据层桥接
          self.analyst = HyperliquidPerpAnalyst(config)  # Analyst
          self.bull_researcher = BullResearcher(config)  # 复用
          self.bear_researcher = BearResearcher(config)  # 复用
          self.trader = CryptoTraderAgent(config)       # 新增/扩展
          self.risk_mgmt = CryptoRiskManager(config)    # 新增/扩展
          self.portfolio_manager = PortfolioManager(config)  # 路由
          
      def propagate(self, symbol: str, date: str) -> tuple[dict, str]:
          """
          端到端分析流程
          返回 (analysis_result, decision)
          """
          # 1. 数据获取
          hl_data = self.data.get(symbol, date)
          
          # 2. Analyst 分析
          analyst_report = self.analyst.analyze(symbol, date, hl_data)
          
          # 3. Researcher 辩论
          bull_case = self.bull_researcher.research(analyst_report)
          bear_case = self.bear_researcher.research(analyst_report)
          
          # 4. Trader 汇总
          decision = self.trader.decide(symbol, analyst_report, bull_case, bear_case)
          
          # 5. Risk 评估
          risk_report = self.risk_mgmt.evaluate(decision)
          
          # 6. Portfolio Manager 审批
          final_decision = self.portfolio_manager.approve(decision, risk_report)
          
          return analyst_report, final_decision
  ```

### T1.6.2 `graph/data_bridge.py` — 数据层桥接
- [ ] `HyperliquidDataBridge` 类
  - 对齐原项目的 `DataSource` 接口
  - 提供统一的数据获取方法
  ```python
  class HyperliquidDataBridge:
      def __init__(self, config: dict):
          self.hl_data = get_hl_data  # M1.2 的统一入口
      
      def get(self, symbol: str, date: str) -> dict:
          """获取并聚合所有 HL 数据"""
          return get_hl_data(symbol, date, intervals=["1h", "4h", "1d"])
  ```

### T1.6.3 `graph/trader_agent.py` — Crypto 交易员
- [ ] `CryptoTraderAgent`（扩展或新建）
  - 接收 Analyst report + Bull/Bear cases
  - 输出交易决策：
    ```python
    {
        "action": "long | short | close | hold",
        "size_pct": 0.0-1.0,
        "leverage": 1-20,
        "entry_reason": "...",
        "risk_adjusted": bool,
    }
    ```
  - 逻辑：综合多空辩论，权重计算最终方向

### T1.6.4 `graph/risk_manager.py` — Crypto 风险管理
- [ ] `CryptoRiskManager`（Phase 3 简化版，Phase 1 只做基础检查）
  - 基础敞口检查（Phase 3 再完整实现）
  - 波动率阈值检查
  ```python
  class CryptoRiskManager:
      def evaluate(self, decision: dict, hl_data: dict) -> dict:
          """
          返回风控评估报告：
          {
              "approved": bool,
              "warnings": [...],
              "adjustments": {...},
          }
          """
  ```

### T1.6.5 复用原 Graph 模块
- [ ] 分析原项目 `tradingagents/graph/` 结构
  - `setup.py` — Graph 构建
  - `propagation.py` — 前向传播
  - `reflection.py` — 反思机制
- [ ] 确定哪些可复用，哪些需替换
- [ ] 创建 `graph/compat.py` — 兼容层
  ```python
  # 复用原模块
  from tradingagents.graph.propagation import propagate
  from tradingagents.graph.reflection import reflect
  # 替换数据源
  from .data_bridge import HyperliquidDataBridge
  ```

### T1.6.6 配置路由
- [ ] `graph/trading_graph_factory.py` — Graph 工厂
  ```python
  def create_graph(config: dict):
      if config.get("mode") == "crypto":
          return CryptoTradingAgentsGraph(config)
      else:
          from tradingagents.graph.trading_graph import TradingAgentsGraph
          return TradingAgentsGraph(config)
  ```

### T1.6.7 集成测试
- [ ] `tests/test_crypto_graph.py`
  - 完整 `propagate("BTC", "2026-03-25")` 运行
  - 验证返回格式
  - 验证各步骤输出

---

## 交付物

| 文件 | 说明 |
|------|------|
| `graph/crypto_trading_graph.py` | 主 Graph 类 |
| `graph/data_bridge.py` | 数据层桥接 |
| `graph/trader_agent.py` | Crypto 交易员 |
| `graph/risk_manager.py` | 简化风控（Phase 1） |
| `graph/trading_graph_factory.py` | Graph 工厂 |
| `graph/compat.py` | 原模块兼容层 |
| `tests/test_crypto_graph.py` | 集成测试 |

---

## 验收标准

- [ ] `CryptoTradingAgentsGraph(config).propagate("BTC", "2026-03-25")` 返回 tuple(dict, str)
- [ ] 第一个元素包含 `summary` / `direction` / `signals` / `metrics` / `narrative`
- [ ] 第二个元素是最终交易决策
- [ ] `create_graph(config)` 根据 mode 返回正确实例
- [ ] 集成测试通过

---

## 与原项目的关系

Phase 1 **不修改**原项目任何文件。所有复用通过 import 或适配器模式实现：
- 原 `BullResearcher` → 直接 import 复用
- 原 `PortfolioManager` → 通过 `mode` 路由到原类
- 原 `setup/propagation/reflection` → 不复用（Crypto 流程差异大）

---

## 预计工时

| 子任务 | 预计时间 |
|--------|---------|
| T1.6.1 crypto_trading_graph.py | 3 小时 |
| T1.6.2 data_bridge.py | 1 小时 |
| T1.6.3 trader_agent.py | 2 小时 |
| T1.6.4 risk_manager.py | 2 小时 |
| T1.6.5 原模块复用分析 | 2 小时 |
| T1.6.6 配置路由 | 1 小时 |
| T1.6.7 集成测试 | 2 小时 |
| **合计** | **~13 小时（2 天）** |
