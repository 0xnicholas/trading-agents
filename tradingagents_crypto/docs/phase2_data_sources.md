# Phase 2 Data Sources Verification

**Date**: 2026-04-01
**VM Network**: Restricted (China region outbound blocking)

---

## API Access Status

| API | Status | Notes |
|-----|--------|-------|
| Alternative.me Fear & Greed | ✅ Available | v1 endpoint works |
| CoinGecko | ❌ Blocked | Connection reset by peer |
| Binance Futures | ❌ Blocked | Connection timed out |
| Jupiter | ❌ Blocked | Connection timed out |
| DeFiLlama | ❓ Untested | — |
| GeckoTerminal | ❓ Untested | — |

---

## Revised Data Sources

### Alternative.me Fear & Greed ✅

- **Endpoint**: `https://api.alternative.me/fng/`
- **Method**: `GET`
- **Returns**: `{"data": [{"value": 8, "value_classification": "Extreme Fear"}]}`
- **Confidence**: 0.5 (free data)
- **Works**: ✅

### CoinCap API (NEW PRIMARY) ✅

**CoinCap is used as CoinGecko alternative (accessible from VM)**

| Data | Endpoint | Example |
|------|----------|---------|
| BTC Dominance | `GET /v2/assets` | Returns market cap % |
| ETH Price | `GET /v2/assets/ethereum` | OHLCV data |
| SOL Price | `GET /v2/assets/solana` | Real-time price |
| ETH Staking | `GET /v2/assets/ethereum` | Has staking info |
| Stablecoins | `GET /v2/assets?ids= tether,usd-coin` | Supply data |

**Base URL**: `https://api.coincap.io`
**Rate Limit**: 300 requests/min (free)
**Confidence**: 0.75 (free but stable)

### Bybit Funding Rates (NEW PRIMARY) ✅

**Bybit is used as Binance alternative (accessible from VM)**

| Data | Endpoint |
|------|----------|
| ETH-PERP Funding | `GET /v5/market/tickers?category=linear&symbol=ETHUSDT` |

**Base URL**: `https://api.bybit.com`
**Rate Limit**: 600 requests/min (free)
**Confidence**: 0.85 (official exchange)

### Solana Data Options

Since Jupiter is blocked, options:

| Option | Status | Notes |
|--------|--------|-------|
| Raydium API | ❓ Untested | DEX on Solana |
| CoinCap SOL | ✅ Available | Simple price |
| GeckoTerminal | ❓ Untested | DEX aggregator |

**Decision**: Use CoinCap for SOL price (simple), test GeckoTerminal for DEX data.

---

## Updated API Mapping

| Original Source | Alternative | Data | Confidence |
|----------------|------------|------|-----------|
| CoinGecko | CoinCap.io | ETH/SOL prices, BTC dominance | 0.75 |
| Binance Futures | Bybit | ETH-PERP funding rate | 0.85 |
| Alternative.me | Alternative.me | Fear & Greed | 0.5 |
| Jupiter (blocked) | CoinCap + GeckoTerminal | SOL price + DEX data | 0.7 |
| Etherscan | CoinCap | Stablecoin flows | 0.5 |
| DeFiLlama | ❌ Not tested | TVL | — |

---

## Next Steps

1. Test CoinCap.io API availability
2. Test Bybit API availability
3. Test GeckoTerminal API
4. Update SPEC.md with new data sources
5. Update TASK.md accordingly

---

## Testing Commands

```bash
# CoinCap
curl -s "https://api.coincap.io/v2/assets/ethereum" | jq

# Bybit
curl -s "https://api.bybit.com/v5/market/tickers?category=linear&symbol=ETHUSDT" | jq

# GeckoTerminal
curl -s "https://api.geckoterminal.com/api/v1/dexes/pools/solana" | jq
```
