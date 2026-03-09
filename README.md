# Kalshi Weather Edge System v2

Multi-model consensus-based edge detection for Kalshi weather markets.

## Philosophy

**Edge exists when:**
1. Multiple weather models AGREE on a temperature (low spread)
2. Kalshi market price DIVERGES from model consensus

**No edge when:**
1. Models strongly disagree (high uncertainty = skip)
2. Market prices align with model consensus

## Quick Start

```bash
# Scan all cities for tomorrow
python weather_edge_v2.py

# Scan today
python weather_edge_v2.py --today

# Scan specific city/date
python weather_edge_v2.py --city chicago --date 2026-03-06

# Output as JSON
python weather_edge_v2.py --json
```

## Data Sources

### Weather Models (5 sources)
| Model | Source | Notes |
|-------|--------|-------|
| NWS | api.weather.gov | US National Weather Service, hourly forecasts |
| ECMWF | Open-Meteo | European model, generally most accurate |
| GFS | Open-Meteo | US Global Forecast System |
| ICON | Open-Meteo | German model |
| GEM | Open-Meteo | Canadian model |

### Real-Time Observations
- METAR data from Aviation Weather Center
- Used for mid-day edge adjustments

## Station Mapping

**IMPORTANT:** Kalshi uses specific measurement stations:

| City | Kalshi Station | Notes |
|------|---------------|-------|
| Chicago | **KMDW** (Midway) | NOT O'Hare (KORD) |
| Miami | KMIA | Miami International |
| NYC | **Central Park** | NOT an airport! KNYC automated |
| Austin | KAUS | Austin-Bergstrom |
| Denver | KDEN | Denver International |
| LA | KLAX | LAX |

## Edge Criteria

### Agreement Levels
| Level | Spread | Action |
|-------|--------|--------|
| Strong | ≤2°F | High confidence bets |
| Moderate | 2-4°F | Standard confidence |
| Weak | 4-6°F | Reduce size or skip |
| Divergent | >6°F | **SKIP** - too uncertain |

### Edge Thresholds
| Edge | Recommendation |
|------|---------------|
| ≥15% | **Strong Buy** |
| ≥8% | Buy |
| <8% | Skip (insufficient) |
| <-15% | Avoid (overpriced) |

## Output Example

```
🔍 EDGE ANALYSIS: CHICAGO - 2026-03-06
============================================================

📊 MODEL COMPARISON:
──────────────────────────────────────────────────
  NWS                  │  42.0°F
  ECMWF IFS04          │  43.2°F
  GFS SEAMLESS         │  41.8°F
  ICON SEAMLESS        │  42.5°F
  GEM SEAMLESS         │  42.1°F
──────────────────────────────────────────────────
  CONSENSUS            │  42.3°F
  Spread               │   1.4°F
  Agreement            │ STRONG

✅ EDGE FOUND - 1 opportunity(ies):

  🔥 KXHIGHCHI-06MAR26-B40.5
     Threshold: >= 40.5°F
     Consensus: 42.3°F | Market: 68% | Model: 85%
     EDGE: +17.0% | Confidence: HIGH
     → Strong edge with model consensus
```

## Bias Tracking

After each settlement, update the bias model:

```python
from weather_edge_v2 import record_settlement

record_settlement(
    city='chicago',
    date='2026-03-05',
    actual_high=43,
    forecasts=[
        {'model': 'NWS', 'high_temp': 42},
        {'model': 'ECMWF IFS04', 'high_temp': 43.2},
        # ... other models
    ]
)
```

This tracks:
- Mean bias per model (systematic over/under forecasting)
- MAE (Mean Absolute Error) per model
- Historical accuracy for confidence weighting

## Files

| File | Purpose |
|------|---------|
| `weather_edge_v2.py` | Main scanner (v2 with multi-model) |
| `bias_model_v2.json` | Model accuracy tracking |
| `nws_forecast.py` | Legacy NWS-only scanner |
| `edge_scanner.py` | Legacy single-model scanner |

## Algorithm

1. **Fetch** forecasts from NWS + 4 Open-Meteo models
2. **Calculate** consensus (average) and spread (disagreement)
3. **Classify** agreement level (strong/moderate/weak/divergent)
4. **Fetch** current Kalshi market prices
5. **Compare** model probability vs market price
6. **Flag** opportunities where:
   - Agreement is strong/moderate
   - Edge ≥ 8%
7. **Check** current temps for mid-day adjustments

## Notes

- NYC is Central Park, not an airport - microclimate matters
- Chicago uses Midway (KMDW), not O'Hare
- Morning forecasts (before 11am) are less reliable for same-day
- If running 3°F+ hot/cold vs expected by noon, models may be wrong
