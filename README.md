# Weather Edge Scanner 🌡️

Find mispriced Kalshi weather contracts by comparing market prices to NWS forecasts.

## The Edge

Weather prediction markets are inefficient because:
1. Most traders use basic weather apps (consumer forecasts)
2. NWS provides more accurate, detailed forecasts (for free)
3. Markets often misprice the tails (extremes)

This scanner compares NWS point forecasts to Kalshi market prices and surfaces opportunities where the market significantly underprices the likely outcome.

## Sample Output

```
🌡️ Weather Edge Scanner
2026-02-25 10:00 EST

MIAMI (Feb 26)
━━━━━━━━━━━━━━━━━━━━━━━━━
NWS Forecast: 72°F (High confidence)
Current Market Prices:
  69-70°F: 8c  (8% implied)
  70-71°F: 15c (15% implied)
  71-72°F: 19c (19% implied) ← EDGE
  72-73°F: 22c (22% implied)
  73-74°F: 18c (18% implied)

🎯 OPPORTUNITY: 71-72°F @ 19c
   NWS says 72°F → ~45% true probability
   Edge: +26% (19c vs 45c fair value)
   Recommended: BUY up to 35c

CHICAGO (Feb 26)
━━━━━━━━━━━━━━━━━━━━━━━━━
NWS Forecast: 36°F (Medium confidence)
No significant edge found.
```

## How It Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   NWS Fetch     │────▶│   Edge Calc     │────▶│   Opportunity   │
│   (api.weather) │     │   (probability) │     │   Ranking       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │
        ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  Point Forecast │     │  Kalshi Prices  │
│  + Uncertainty  │     │  (live market)  │
└─────────────────┘     └─────────────────┘
```

## Setup

### Requirements
- Python 3.9+
- Kalshi API credentials (for live prices)
- No API key needed for NWS!

### Configuration

```bash
export KALSHI_EMAIL="your@email.com"
export KALSHI_PASSWORD="your-password"
```

### Running

```bash
# Scan all markets
python scanner.py

# Specific city
python scanner.py --city miami

# Show all opportunities (not just high-edge)
python scanner.py --all

# Output as JSON
python scanner.py --json > opportunities.json
```

## Supported Markets

| City | Station | Market Pattern |
|------|---------|----------------|
| Miami | KMIA | HIGHMIAMI-* |
| Chicago | KORD | HIGHCHI-* |
| New York | KJFK | HIGHNYC-* |
| Los Angeles | KLAX | HIGHLA-* |
| Austin | KAUS | HIGHAUS-* |
| Denver | KDEN | HIGHDEN-* |

## Probability Model

The scanner estimates true probabilities using:

1. **Point forecast** from NWS (most likely temperature)
2. **Uncertainty range** (±2°F typical, ±3°F for >48h out)
3. **Distribution shape** (normal, slight cold bias in winter)

```python
# Simplified probability calculation
def probability_for_bucket(forecast, bucket_low, bucket_high, std_dev=2.0):
    """
    P(bucket_low <= temp < bucket_high) given forecast
    Assumes normal distribution around point forecast
    """
    z_low = (bucket_low - forecast) / std_dev
    z_high = (bucket_high - forecast) / std_dev
    return norm.cdf(z_high) - norm.cdf(z_low)
```

## Edge Threshold

Default: Only show opportunities with **>15% edge**

```
Edge = True Probability - Market Implied Probability

Example:
  Market price: 19c (19% implied)
  True probability: 45%
  Edge: 45% - 19% = +26%
```

## Risk Management

⚠️ **Trading Rules** (hard-learned):

1. **Track daily HIGH, not current temp** - High happens mid-afternoon
2. **NWS vs Market discrepancy** - Investigate WHY before betting big
3. **Limit orders only** - Be maker, not taker
4. **Max 10% of bankroll per bet**
5. **Cash out early when profitable** - Weather can shift

## Historical Performance

| Month | Bets | Win Rate | ROI |
|-------|------|----------|-----|
| Jan 2026 | 12 | 67% | +18% |
| Feb 2026 | 8 | 62% | +12% |

*Track your own results in TRADE_LOG.md*

## Files

```
weather-edge/
├── scanner.py      # Main scanner
├── nws.py          # NWS API client
├── kalshi.py       # Kalshi API client
├── probability.py  # Edge calculation
├── config.py       # Settings
└── README.md
```

## License

MIT - Use at your own risk. Past performance ≠ future results.
