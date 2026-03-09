# Kalshi Edge Strategy

**Goal:** Double $500 → $1,000 in one week  
**Start Date:** Feb 18, 2026  
**End Date:** Feb 25, 2026

---

## Core Principles (from profitable traders)

1. **LIMIT ORDERS ONLY** - Be maker, not taker (better prices, no fees)
2. **NICHE FOCUS** - Pick 1-2 market types and master them
3. **EV THINKING** - Find mispriced probabilities, not "winners"
4. **AVOID SPORTS** - Too efficient, hard to beat long-term
5. **READ CONTRACT RULES** - Edge often in resolution details

---

## Strategy 1: Temperature Markets

### The Edge
Most traders don't understand:
- NWS station locations (KNYC = Central Park, not JFK)
- Celsius/Fahrenheit conversion quirks
- 5-minute vs hourly station differences
- Which forecast models are most accurate

### Execution
1. Pull NWS forecast for target city
2. Compare to Kalshi market prices
3. If forecast shows 90% confidence in temp range but Kalshi priced at 70¢ = 20% edge
4. Place limit order slightly below current price
5. Wait for resolution

### Key Cities
| City | Station | Notes |
|------|---------|-------|
| NYC | KNYC | Central Park - can differ from airport |
| Chicago | KMDW | Midway Airport |
| Miami | KMIA | MIA Airport |
| Denver | KDEN | DEN Airport |

### Today's Data (Feb 18)
- **NYC:** High 45°F (rainy/foggy)
- **Chicago:** High 65°F (unseasonably warm!)
- **Miami:** High 77°F (sunny)
- **Denver:** High 54°F (chance snow)

---

## Strategy 2: Trump Mention Markets

### The Edge
- You can predict what Trump will say
- Place limit orders BEFORE speech starts
- Exit positions when speech begins (adverse selection)

### High-Probability Phrases
- "fake news", "mainstream media", "radical left"
- "Biden", "Democrats", "China"
- "beautiful", "tremendous", "incredible"
- "border", "immigration", "illegal"

### Upcoming Events
| Date | Time | Event | Importance |
|------|------|-------|------------|
| Feb 18 | 3:00 PM | Black History Month Reception | MEDIUM |
| **Feb 24** | **9:00 PM** | **State of the Union** | **CRITICAL** |

### State of the Union Strategy
This is THE event. Every word will be tracked. Kalshi will have massive mention markets.

**Prep (before Feb 24):**
1. Research historical SOTU word frequencies
2. Track leaked talking points
3. Watch for administration hints on themes
4. Position in high-probability mentions early (24-48h before)

---

## Strategy 3: News Speed

### The Edge
When news breaks, you have 30-60 seconds before Kalshi prices adjust.

### Hot Markets Now
1. **Government Shutdown** - DHS funding lapsed, TSA unpaid
2. **DOGE Announcements** - Agency cuts coming
3. **Tariffs** - Ongoing threats to Canada/Mexico

### Sources (speed-ranked)
1. @WhiteHouse, @POTUS tweets
2. Reuters breaking news
3. @AP breaking news
4. Bloomberg (if available)

---

## Week 1 Execution Plan

| Day | Action | Target Bet | Risk |
|-----|--------|------------|------|
| **Tue 2/18** | Position on Trump 3pm speech | $50-100 | Low |
| **Wed 2/19** | Weather markets (Chicago warm) | $100 | Low |
| **Thu 2/20** | News events (shutdown?) | $100 | Med |
| **Fri 2/21** | Stack positions for SOTU | $100 | Med |
| **Sat-Sun** | Research SOTU themes | $0 | N/A |
| **Mon 2/24** | SOTU mention markets | $200+ | High |
| **Tue 2/25** | SOTU follow-up trades | Remaining | Med |

---

## Risk Management

- **Max single bet:** $150 (30% of bankroll)
- **Daily loss limit:** $100
- **Position sizing:** Scale with confidence
- **Always use limit orders**

---

## Success Metrics

- Week 1: $500 → $1,000 (100% return)
- Or: 3-4 winning trades at 30-50% each

---

## Tools

- `weather_monitor.py` - NWS forecast vs Kalshi prices
- `trump_tracker.py` - Speech calendar and common phrases
- `news_speed.py` - Breaking news sources

---

*Strategy based on research from traders making $100k+/month on Kalshi*
