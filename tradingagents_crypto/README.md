# TradingAgents Crypto

**Multi-Agent LLM Trading Framework for Cryptocurrency Perpetual Contracts**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

TradingAgents Crypto is a specialized fork of [TradingAgents](https://github.com/TauricResearch/TradingAgents) focused on cryptocurrency perpetual contracts. It leverages multi-agent LLM architecture to analyze Hyperliquid, Ethereum, and Solana markets.

## Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ Complete | Hyperliquid single-chain implementation |
| Phase 2 | ⏭️ Skipped | Multi-chain expansion |
| Phase 3 | ✅ Complete | Risk management & backtesting |
| Phase 4 | ✅ Complete | Production infrastructure |

## Features

- **Multi-Agent Architecture**: Specialized analysts for each blockchain
- **Parallel Execution**: Concurrent analyst processing with timeout control
- **Risk Management**: Historical volatility analysis, liquidation risk assessment
- **Backtesting Engine**: Strategy backtesting with slippage/fee simulation
- **Paper Trading**: Simulated trading with full order book
- **Live Trading**: Hyperliquid integration for real trading
- **Observability**: Structured logging, Prometheus metrics, health checks
- **Containerized**: Docker + docker-compose deployment

## Supported Chains

| Chain | Status | Features |
|-------|--------|----------|
| Hyperliquid | ✅ Primary | Perpetual contracts, funding, OI, orderbook |
| Ethereum | 🔵 Extension | On-chain analytics, gas, TVL |
| Solana | 🔵 Extension | DEX analysis, meme tokens |

## Installation

```bash
# Clone repository
git clone https://github.com/0xnicholas/trading-agents.git
cd trading-agents

# Create virtual environment
conda create -n tradingagents python=3.11
conda activate tradingagents

# Install dependencies
cd tradingagents_crypto
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Environment Variables

```bash
OPENAI_API_KEY=...       # OpenAI GPT models
GOOGLE_API_KEY=...       # Google Gemini
ANTHROPIC_API_KEY=...    # Anthropic Claude
```

## Quick Start

```python
from tradingagents_crypto.graph.crypto_trading_graph import CryptoTradingGraph
from tradingagents_crypto.config.default_config import DEFAULT_CONFIG

# Initialize
config = DEFAULT_CONFIG.copy()
config["trading_mode"] = "paper"  # or "live"
ta = CryptoTradingGraph(debug=True, config=config)

# Run analysis
result, decision = ta.propagate("BTC", "2026-04-01")
print(decision)
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Chain-Specific Analysts（并行）                       │
│  ├─ Hyperliquid Perp Analyst                          │
│  ├─ Ethereum OnChain Analyst（扩展）                   │
│  └─ Solana DEX Analyst（扩展）                         │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│  Bull/Bear Researchers（辩论）                        │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│  Trader Agent                                        │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│  Risk Management                                    │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│  Portfolio Manager + Approval Workflow               │
└─────────────────────────────────────────────────────┘
    ↓
PaperTrading / HyperliquidConnector
```

## Project Structure

```
tradingagents_crypto/
├── agents/              # Agent implementations
│   ├── analysts/        # Chain-specific analysts
│   ├── researchers/     # Bull/Bear researchers
│   ├── risk_mgmt/      # Risk management agents
│   ├── traders/        # Trading agents
│   └── managers/       # Portfolio managers
├── graph/              # LangGraph workflow
│   └── nodes/          # Graph nodes
├── dataflows/          # Data layer
│   └── hyperliquid/    # Hyperliquid API
├── backtest/          # Backtesting engine
├── trading/           # Trading execution
│   ├── paper_engine.py
│   ├── hyperliquid.py
│   └── approval.py
├── alerts/            # Alert system
├── utils/             # Logging, metrics
├── api/              # FastAPI health checks
└── config/           # Configuration
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=tradingagents_crypto --cov-report=html
```

## Trading Modes

### Paper Trading (Default)
```python
config["trading_mode"] = "paper"
```

### Live Trading (Requires Approval)
```python
config["trading_mode"] = "live"
config["approval_required"] = True
```

## Documentation

- [AGENTS.md](./AGENTS.md) — Architecture and agent design
- [STATUS.md](./STATUS.md) — Project status and milestones
- [plans/](./plans/) — Detailed development plans

## Dependencies

- **Python**: 3.11+
- **LLM Providers**: OpenAI GPT-4o, Google Gemini, Anthropic Claude
- **Data**: Hyperliquid Python SDK
- **Graph**: LangGraph
- **Metrics**: Prometheus
- **Container**: Docker, docker-compose

## License

MIT License — see [LICENSE](../LICENSE)

## References

- [TradingAgents (Original)](https://github.com/TauricResearch/TradingAgents)
- [Hyperliquid SDK](https://github.com/hyperliquid-dex/hyperliquid-python-sdk)
- [arXiv Paper](https://arxiv.org/abs/2412.20138)

---

*For research purposes only. Trading performance may vary.*
