# Phase 2 技术规格说明书

**版本**: v1.0
**日期**: 2026-04-01
**状态**: 待审查

---

## 1. 概述

### 1.1 目标

在 Hyperliquid 单链基础上，新增 Ethereum 和 Solana 数据层及对应 Analyst，形成跨链分析能力。

### 1.2 核心设计决策

| 决策 | 说明 |
|------|------|
| Solana = 现货 DEX | 不做 Solana 永续合约，专注 Memecoin 流动性分析 |
| 跨链并行执行 | Chain-Specific Analyst 并行运行，Macro Analyst 汇总 |
| 置信度标注 | 所有数据必须标注 confidence 字段，近似数据 0.4-0.6 |
| 降级策略 | 单链失败不影响其他链，置信度自动下调 |

---

## 2. 系统架构

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Crypto Trading Graph                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ HL Analyst   │  │ ETH Analyst  │  │ SOL Analyst │    │
│  │ (Phase 1)  │  │  (Phase 2)  │  │  (Phase 2) │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │             │
│         └─────────────────┼─────────────────┘             │
│                           │                                   │
│                    ┌──────▼──────┐                         │
│                    │ Macro Analyst│                         │
│                    │  (Phase 2)  │                         │
│                    └──────┬──────┘                         │
│                           │                                   │
│                    ┌──────▼──────┐                         │
│                    │Trader Agent │                          │
│                    └─────────────┘                           │
└─────────────────────────────────────────────────────────────┘

Data Sources:
  Hyperliquid SDK     Ethereum APIs           Solana APIs
  - CoinGecko         - Binance Futures      - Jupiter
  - Alternative.me     - Etherscan           - GeckoTerminal
  - (Phase 1)         - DeFiLlama          - Raydium
```

### 2.2 模块关系

```
dataflows/
├── hyperliquid/     ← Phase 1 (existing)
├── ethereum/
│   ├── price.py     ← CoinGecko
│   ├── funding.py   ← Binance Futures
│   ├── onchain.py   ← Etherscan, DeFiLlama, CoinGecko
│   └── main.py       ← 统一入口
└── solana/
    ├── price.py     ← Jupiter
    ├── dex.py        ← Jupiter, Raydium
    ├── meme.py       ← GeckoTerminal
    └── main.py       ← 统一入口

agents/analysts/
├── hyperliquid_perp_analyst.py  ← Phase 1
├── ethereum_onchain_analyst.py   ← Phase 2
├── solana_dex_analyst.py        ← Phase 2
└── cross_chain_macro_analyst.py ← Phase 2
```

---

## 3. 数据层规格

### 3.1 Ethereum 数据

#### 3.1.1 价格数据 (T2.1.1)

**模块**: `dataflows/ethereum/price.py`

**数据源**: CoinGecko API
- 端点: `GET /api/v3/coins/ethereum/ohlc`
- 参数: `vs_currency=usd&days=7`

**函数**: `get_eth_price(days: int = 7) -> pd.DataFrame`
- 返回: DataFrame with [timestamp, open, high, low, close, volume]
- TTL: 300s
- 置信度: 0.75

**偏差检测**: `check_price_deviation(eth_price: float, hl_mark_px: float) -> dict`
- 偏差 > 1%: 日志警告 + confidence 下调 0.1

#### 3.1.2 资金费率 (T2.1.4)

**模块**: `dataflows/ethereum/funding.py`

**数据源**: Binance Futures API
- 端点: `GET /fapi/v1/fundingRate?symbol=ETHUSDT`

**函数**: `get_binance_funding() -> dict`
```python
{
    "symbol": "ETHUSDT",
    "funding_rate": 0.0001,        # 8h rate
    "annualized": 0.1095,          # rate * 3 * 365
    "next_funding_time": 1234567890,
    "confidence": 0.9
}
```

#### 3.1.3 链上数据 (T2.1.7-2.1.10)

**模块**: `dataflows/ethereum/onchain.py`

| 数据 | 函数 | 数据源 | TTL | 置信度 |
|------|------|--------|-----|--------|
| Gas 价格 | `get_gas_price()` | Etherscan Gas API | 60s | 0.8 |
| ETH 质押量 | `get_staking_ratio()` | CoinGecko | 300s | 0.75 |
| DeFi TVL | `get_defi_tvl()` | DeFiLlama API | 300s | 0.8 |
| 活跃地址（可选）| `get_active_addresses()` | CoinGecko on-chain | 600s | 0.5 |

#### 3.1.4 ETH 主入口 (T2.1.11)

**模块**: `dataflows/ethereum/main.py`

**函数**: `get_eth_data(symbol: str = "ETH") -> dict`
```python
{
    "symbol": "ETH",
    "spot_price": {...},       # from price.py
    "funding": {...},          # from funding.py
    "onchain": {
        "gas_price": {...},
        "staking_ratio": {...},
        "defi_tvl": {...},
    },
    "timestamp": 1234567890
}
```

---

### 3.2 Solana 数据

#### 3.2.1 价格数据 (T2.2.1)

**模块**: `dataflows/solana/price.py`

**数据源**: Jupiter Price API
- 端点: `GET /v1/price?ids=SOL&vsToken=USDT`

**函数**: `get_sol_price() -> dict`
```python
{
    "symbol": "SOL",
    "price": 150.0,
    "change_24h_pct": 5.2,
    "confidence": 0.85
}
```

#### 3.2.2 DEX 流动性 (T2.2.2-2.2.3)

**模块**: `dataflows/solana/dex.py`

**数据源**: 
- 主要: Jupiter DEX API
- 备选: Raydium Subgraph (The Graph)

**函数**: `get_dex_liquidity(token: str) -> dict`
```python
{
    "token": "SOL",
    "jupiter_tvl": 50_000_000,
    "raydium_tvl": 30_000_000,
    "total_tvl": 80_000_000,
    "confidence": 0.8
}
```

#### 3.2.3 Meme 币热度 (T2.2.4)

**模块**: `dataflows/solana/meme.py`

**数据源**: GeckoTerminal API
- 端点: `GET /api/v1/on_dexes/pools?network=solana`

**函数**: `get_meme_coins(limit: int = 10) -> list[dict]`
```python
[{
    "symbol": "DOGE",
    "name": "Dogwifhat",
    "tvl_usd": 100_000_000,
    "volume_24h": 50_000_000,
    "price": 2.5,
    "change_24h_pct": 15.2,
    "confidence": 0.7
}]
```

#### 3.2.4 Solana 主入口 (T2.2.6)

**模块**: `dataflows/solana/main.py`

**函数**: `get_sol_data(symbol: str = "SOL") -> dict`

---

### 3.3 跨链宏观数据

#### 3.3.1 BTC Dominance (T2.5.1)

**模块**: `dataflows/macro/btc_dominance.py`

**数据源**: CoinGecko `/global`
- 端点: `GET /api/v3/global`

**函数**: `get_btc_dominance() -> dict`
```python
{
    "btc_dominance": 52.3,
    "trend_7d": "rising",  # rising / falling / stable
    "confidence": 0.85
}
```

#### 3.3.2 Fear & Greed Index (T2.5.3)

**模块**: `dataflows/macro/fear_greed.py`

**数据源**: Alternative.me
- 端点: `GET /api/v2/fng`

**函数**: `get_fear_greed() -> dict`
```python
{
    "value": 35,
    "label": "恐惧",     # 0-25 极度恐惧, 25-50 恐惧, 50-75 贪婪, 75-100 极度贪婪
    "confidence": 0.5    # 免费数据，置信度低
}
```

#### 3.3.3 Stablecoin Flow (T2.5.4-2.5.5)

**模块**: `dataflows/macro/stablecoin_flow.py`

**数据源**: 
- Etherscan USDT 转账量 (近似)
- CoinGecko 稳定币市值

**函数**: `get_stablecoin_flow() -> dict`
```python
{
    "usdt_supply_change_24h": 500_000_000,
    "total_stablecoin_supply": 150_000_000_000,
    "change_pct": 0.33,
    "verdict": "流入增加，多头信号",
    "confidence": 0.5  # 近似数据
}
```

#### 3.3.4 相关性计算 (T2.5.6-2.5.10)

**模块**: `dataflows/macro/correlation.py`

**数据源**: CoinGecko 每日收盘价

**函数**: `get_correlations() -> dict`
```python
{
    "btc_eth_corr_7d": 0.85,
    "btc_sol_corr_7d": 0.72,
    "verdict": "高相关性，市场同向",
    "confidence": 0.8
}
```

---

## 4. Analyst 规格

### 4.1 Ethereum OnChain Analyst (T2.3.1)

**模块**: `agents/analysts/ethereum_onchain_analyst.py`

**输入数据**:
- ETH 现货价格 (CoinGecko)
- ETH-PERP 资金费率 (Binance)
- Gas 价格 (Etherscan)
- ETH 质押率 (CoinGecko)
- DeFi TVL (DeFiLlama)

**输出 Schema** (`EthereumOnChainReport`):
```python
{
    "summary": str,           # 1-2 句话总结
    "direction": str,         # "bullish" | "bearish" | "neutral"
    "confidence": float,      # 0.0-1.0
    "signals": {
        "gas_sentiment": {"value": str, "confidence": float},
        "staking_ratio": {"value": float, "label": str, "confidence": float},
        "tvl_rank": {"value": float, "label": str, "confidence": float},
        "funding_diff": {"value": float, "note": str, "confidence": float}
    },
    "narrative": str          # 详细分析
}
```

### 4.2 Solana DEX / Meme Analyst (T2.4.1)

**模块**: `agents/analysts/solana_dex_analyst.py`

**输入数据**:
- SOL 价格 (Jupiter)
- DEX 流动性 (Jupiter + Raydium)
- Meme 币热度 (GeckoTerminal)

**输出 Schema** (`SolanaDexReport`):
```python
{
    "summary": str,
    "direction": str,
    "confidence": float,
    "signals": {
        "meme_liquidity": {"value": str, "confidence": float},
        "meme_turnover": {"value": float, "label": str, "confidence": float},
        "sol_momentum": {"value": float, "label": str, "confidence": float},
        "dex_volume_rank": {"value": int, "label": str, "confidence": float}
    },
    "narrative": str
}
```

### 4.3 Cross-Chain Macro Analyst (T2.5.11)

**模块**: `agents/analysts/cross_chain_macro_analyst.py`

**输入数据**:
- BTC Dominance (CoinGecko)
- Fear & Greed (Alternative.me)
- Stablecoin Flow (Etherscan + CoinGecko)
- 相关性 (CoinGecko)

**输出 Schema** (`CrossChainMacroReport`):
```python
{
    "summary": str,
    "confidence": float,
    "market_regime": str,      # "risk_on" | "risk_off" | "neutral"
    "btc_dominance": {...},
    "fear_greed": {...},
    "stablecoin_flow": {...},
    "cross_chain_correlation": {...},
    "narrative": str
}
```

---

## 5. Graph 升级规格

### 5.1 多链并行执行 (T2.6.1-2.6.2)

**修改文件**: `graph/crypto_trading_graph.py`

**新增**: 
```python
async def run_parallel_chains(symbol: str, llm, chains: list[str]):
    """并行执行多个 Chain Analyst"""
    tasks = []
    if "hyperliquid" in chains:
        tasks.append(run_hl_analyst(symbol, llm))
    if "ethereum" in chains:
        tasks.append(run_eth_analyst(symbol, llm))
    if "solana" in chains:
        tasks.append(run_sol_analyst(symbol, llm))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### 5.2 Trader 多链汇总 (T2.6.4)

**修改文件**: `agents/trader/crypto_trader.py`

**新增**:
```python
def decide_multi_chain(
    hl_report: HyperliquidPerpReport,
    eth_report: EthereumOnChainReport,
    sol_report: SolanaDexReport,
    macro_report: CrossChainMacroReport
) -> TradingDecision:
    """综合多链报告做出交易决策"""
```

---

## 6. 配置规格

### 6.1 多链配置

**新增配置键** (`config/default_config.py`):

```python
@dataclass
class ChainsConfig:
    """多链配置"""
    hyperliquid: ChainConfig = field(default_factory=lambda: ChainConfig(
        enabled=True,
        data_types=["perp", "orderbook", "funding"]
    ))
    ethereum: ChainConfig = field(default_factory=lambda: ChainConfig(
        enabled=True,
        data_types=["onchain", "spot_price", "funding"]
    ))
    solana: ChainConfig = field(default_factory=lambda: ChainConfig(
        enabled=True,
        data_types=["dex", "meme", "spot_price"]
    ))

@dataclass
class ChainConfig:
    """单链配置"""
    enabled: bool = True
    data_types: list[str] = field(default_factory=list)
    timeout_seconds: int = 30
    cache_ttl_seconds: int = 300
```

**环境变量**:
```bash
CHAIN_ETHEREUM_ENABLED=1
CHAIN_SOLANA_ENABLED=1
CHAIN_HYPERLIQUID_ENABLED=1
```

---

## 7. 错误处理

### 7.1 单链失败降级

```python
def get_chain_data_with_fallback(chain: str) -> dict:
    """单链失败时返回降级数据"""
    try:
        return get_chain_data(chain)
    except ChainAPIError as e:
        logger.warning(f"Chain {chain} failed: {e}")
        return {
            "chain": chain,
            "status": "degraded",
            "confidence": max(0.0, base_confidence - 0.3),
            "error": str(e)
        }
```

### 7.2 置信度下调规则

| 错误类型 | 下调幅度 |
|---------|---------|
| API 超时 | -0.1 |
| API 限流 | -0.15 |
| 数据解析失败 | -0.2 |
| 完全不可用 | -0.3 |

---

## 8. API 限流处理

### 8.1 CoinGecko 限流

- 限制: 10-30 calls/min (免费版)
- 处理: 共享缓存 TTL=60s
- 关键端点缓存更长: BTC.D 缓存 TTL=300s

### 8.2 Binance 限流

- 限制: 1200 requests/min
- 处理: 共享 HTTP client

### 8.3 Etherscan 限流

- 限制: 5 calls/sec
- 处理: 串行请求 + 缓存

---

## 9. 目录结构

```
tradingagents_crypto/
├── dataflows/
│   ├── hyperliquid/       ← Phase 1
│   ├── ethereum/
│   │   ├── __init__.py
│   │   ├── price.py       ← T2.1.1
│   │   ├── funding.py     ← T2.1.4
│   │   ├── onchain.py     ← T2.1.7-2.1.10
│   │   └── main.py        ← T2.1.11
│   ├── solana/
│   │   ├── __init__.py
│   │   ├── price.py       ← T2.2.1
│   │   ├── dex.py         ← T2.2.2
│   │   ├── meme.py        ← T2.2.4
│   │   └── main.py        ← T2.2.6
│   └── macro/
│       ├── __init__.py
│       ├── btc_dominance.py    ← T2.5.1
│       ├── fear_greed.py       ← T2.5.3
│       ├── stablecoin_flow.py  ← T2.5.4
│       └── correlation.py      ← T2.5.6-2.5.10
├── agents/analysts/
│   ├── hyperliquid_perp_analyst.py  ← Phase 1
│   ├── ethereum_onchain_analyst.py   ← T2.3.1
│   ├── solana_dex_analyst.py        ← T2.4.1
│   └── cross_chain_macro_analyst.py ← T2.5.11
├── graph/
│   └── crypto_trading_graph.py       ← T2.6 升级
└── config/
    └── default_config.py             ← T2.6 配置升级
```

---

## 10. 修订历史

| 版本 | 日期 | 修订内容 |
|------|------|---------|
| v1.0 | 2026-04-01 | 初始版本 |
