# TRADING BIBLE

*Source: @noisyb0y1's Polymarket guide — adapted for Kalshi*

## Core Philosophy

**Speed + Math beats humans.** No emotions, no FOMO, no stress — just numbers (facts).

---

## The Three Formulas

### 1. EV (Expected Value) — Find the Edge

```
EV = p_true − market_price
```

- `p_true` = your estimated probability (from NWS, data, research)
- `market_price` = current Kalshi YES price

**Rule:** If EV > 0, there's edge. If EV ≤ 0, no trade.

**Example (Weather):**
- NWS says 70% chance of 44°F+ high
- Kalshi YES price: 27¢ (0.27)
- EV = 0.70 − 0.27 = **+0.43** ✅ Strong edge

---

### 2. Kelly Criterion — Size Your Bets

```
f = (p × b − q) / b
```

Where:
- `f` = fraction of bankroll to bet
- `p` = probability of winning (your p_true)
- `q` = probability of losing (1 − p)
- `b` = odds received (payout ratio)

For Kalshi YES bets at price `c`:
- `b = (1 − c) / c` (you pay c, win 1−c)
- Simplified: `f = p − (q × c) / (1 − c)`

**Example:**
- p_true = 0.70, price = 0.27
- b = 0.73 / 0.27 = 2.70
- f = (0.70 × 2.70 − 0.30) / 2.70 = **0.59** (59% of bankroll)

**Half-Kelly Rule:** In practice, use f/2 to reduce variance.

---

### 3. Frank-Wolfe — Portfolio Optimization

```
x_{t+1} = (1−γ)x_t + γ s_t
```

When running multiple positions:
- Don't treat each bet independently
- Balance exposure across all open positions
- Rebalance as odds change

**Practical Rule:** 
- Max 20% of portfolio in any single bet
- Diversify across uncorrelated markets (weather cities, events)
- Cut losers early, let winners ride

---

## Trading Checklist

Before EVERY trade:

1. **[ ] Calculate EV** — Is p_true > market_price?
2. **[ ] Check edge size** — Is EV > 0.10? (minimum 10% edge)
3. **[ ] Run Kelly** — What's the optimal bet size?
4. **[ ] Apply Half-Kelly** — Cut Kelly result in half
5. **[ ] Check portfolio** — Does this exceed 20% of total?
6. **[ ] Verify data source** — Is p_true from reliable source (NWS, official)?
7. **[ ] Log the trade** — Update TRADE_LOG.md IMMEDIATELY

---

## Kalshi-Specific Rules

### Weather Markets
- **Data source:** NWS hourly forecasts (api.weather.gov)
- **Key insight:** Track DAILY HIGH, not current temp
- **Timing:** High usually hits 2-4pm local time
- **Edge window:** NWS updates every hour; market lags

### Event Markets
- **DO NOT BET:** UFC, MMA (too unpredictable — learned the hard way)
- **Careful:** BTC price bets (verify actual prices, volatility kills)
- **Better:** Binary political/policy outcomes with clear resolution

---

## Automation Targets

1. **NWS Polling** — Hourly forecast fetch for tracked cities
2. **Edge Scanner** — Calculate EV across all weather buckets
3. **Alert System** — Telegram ping when EV > 0.15
4. **Position Tracker** — Unified PnL across all open bets
5. **Kelly Calculator** — Auto-size based on bankroll + edge

---

## The 9.7 Second Rule

> "In prediction market trading, 9.7 seconds is an eternity. You already missed the opportunity."

**Translation:** Automate everything possible. The human who notices → opens position → confirms is already too late.

---

## Commandments

1. **No edge, no trade**
2. **Math decides bet size, not gut**
3. **Verify data before trusting memory**
4. **Log every trade immediately**
5. **Cut losers, let winners ride**
6. **Never bet UFC**
7. **Speed wins**

---

*Last updated: 2026-02-25*
