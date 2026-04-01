# M1.3：配置层

**状态**: 🔵 就绪（未开始）
**周期**: Day 3-4
**前置依赖**: M1.1 ✅

---

## 任务目标

创建 `default_config.py`（Crypto 专用配置），实现 `mode="crypto"` 路由逻辑。

---

## 详细子任务

### T1.3.1 创建 `default_config.py`
- [ ] 创建 `tradingagents_crypto/default_config.py`
  ```python
  import os
  
  DEFAULT_CONFIG = {
      # === 模式切换 ===
      "mode": "crypto",  # "stock" | "crypto"
      
      # === 目录配置 ===
      "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
      "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
      "data_cache_dir": os.path.join(
          os.path.abspath(os.path.dirname(__file__)),
          "dataflows", "hyperliquid", "data_cache"
      ),
      
      # === Crypto 专用配置 ===
      "crypto": {
          "primary_chain": "hyperliquid",
          "supported_chains": ["hyperliquid"],  # Phase 2 扩展
          "default_interval": "1h",
          "intervals": ["1h", "4h", "1d"],
          "max_candles_lookback_days": 7,
          
          # Hyperliquid API
          "hl_api_base": "https://api.hyperliquid.xyz",
          "hl_skip_ws": True,
          
          # 数据缓存 TTL（秒）
          "cache_ttl": {
              "candles": 3600,      # 1 小时
              "funding": 300,       # 5 分钟
              "oi": 300,            # 5 分钟
              "orderbook": 0,       # 不缓存（实时）
          },
      },
      
      # === 技术指标配置 ===
      "indicators": {
          "atr_period": 14,
          "rsi_period": 14,
          "rsi_overbought": 70,
          "rsi_oversold": 30,
          "macd_fast": 12,
          "macd_slow": 26,
          "macd_signal": 9,
          "boll_period": 20,
          "boll_std": 2,
          "volume_ma_short": 7,
          "volume_ma_long": 24,
      },
      
      # === LLM 配置（与原项目一致）===
      "llm_provider": "openai",
      "deep_think_llm": "gpt-5.4",
      "quick_think_llm": "gpt-5.4-mini",
      "output_language": "English",
      
      # === 辩论配置 ===
      "max_debate_rounds": 1,
      "max_risk_discuss_rounds": 1,
      "max_recur_limit": 100,
  }
  ```

### T1.3.2 配置加载器
- [ ] `config_loader.py` — 配置加载和合并
  ```python
  def load_config(overrides: dict = None) -> dict:
      """加载默认配置，合并 overrides"""
      config = DEFAULT_CONFIG.copy()
      if overrides:
          deep_merge(config, overrides)
      return config
  
  def is_crypto_mode(config: dict) -> bool:
      return config.get("mode") == "crypto"
  ```

### T1.3.3 路由决策逻辑
- [ ] 在 Agent/Graph 入口添加 mode 检查
  ```python
  # agents/analyst_factory.py
  def get_analyst(config: dict, chain: str):
      if is_crypto_mode(config):
          if chain == "hyperliquid":
              return HyperliquidPerpAnalyst(config)
      else:
          # 原股票模式
          return FundamentalsAnalyst(config)
  ```
- [ ] 在 Graph 入口添加路由
  ```python
  # graph/trading_graph_factory.py
  def create_graph(config: dict):
      if is_crypto_mode(config):
          from .crypto_trading_graph import CryptoTradingAgentsGraph
          return CryptoTradingAgentsGraph(config)
      else:
          from .trading_graph import TradingAgentsGraph
          return TradingAgentsGraph(config)
  ```

### T1.3.4 环境变量配置
- [ ] 支持通过 `.env` 文件覆盖配置
  ```
  # .env.example
  HL_API_BASE=https://api.hyperliquid.xyz
  OPENAI_API_KEY=sk-...
  TRADINGAGENTS_RESULTS_DIR=/path/to/results
  ```
- [ ] 创建 `.env.example` 文件
- [ ] 创建 `load_env.py` 工具函数

### T1.3.5 配置验证
- [ ] `tests/test_config.py` — 验证配置完整性
  - 必填字段存在
  - `mode` 值合法
  - `intervals` 包含 `default_interval`

---

## 交付物

| 文件 | 说明 |
|------|------|
| `default_config.py` | Crypto 默认配置 |
| `config_loader.py` | 配置加载 + 合并 |
| `trading_graph_factory.py` | Graph 路由工厂 |
| `load_env.py` | 环境变量加载 |
| `.env.example` | 环境变量示例 |
| `tests/test_config.py` | 配置测试 |

---

## 验收标准

- [ ] `load_config()` 返回完整配置 dict
- [ ] `is_crypto_mode(config)` 正确判断
- [ ] `create_graph(config)` 根据 mode 返回正确 Graph 实例
- [ ] `.env` 文件可覆盖默认配置
- [ ] 配置测试全部通过

---

## 与 M1.4 的并行关系

M1.3 和 M1.4 可并行开发（M1.3 建立配置，M1.4 依赖配置计算指标）。

---

## 预计工时

| 子任务 | 预计时间 |
|--------|---------|
| T1.3.1 default_config.py | 30 分钟 |
| T1.3.2 config_loader.py | 1 小时 |
| T1.3.3 路由逻辑 | 1 小时 |
| T1.3.4 环境变量 | 30 分钟 |
| T1.3.5 配置验证 | 1 小时 |
| **合计** | **~4 小时** |
