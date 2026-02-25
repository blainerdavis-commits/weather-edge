#!/usr/bin/env python3
"""
Weather Edge Scanner - Find mispriced Kalshi weather contracts
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import math

# NWS stations for supported cities
STATIONS = {
    "miami": {"station": "KMIA", "gridpoint": "MFL/110,50", "market": "HIGHMIAMI"},
    "chicago": {"station": "KORD", "gridpoint": "LOT/76,73", "market": "HIGHCHI"},
    "nyc": {"station": "KJFK", "gridpoint": "OKX/33,37", "market": "HIGHNYC"},
    "la": {"station": "KLAX", "gridpoint": "LOX/154,44", "market": "HIGHLA"},
    "austin": {"station": "KAUS", "gridpoint": "EWX/156,91", "market": "HIGHAUS"},
    "denver": {"station": "KDEN", "gridpoint": "BOU/62,60", "market": "HIGHDEN"},
}


@dataclass
class Forecast:
    city: str
    date: str
    high_temp: float
    confidence: str  # high, medium, low
    source: str


@dataclass
class MarketPrice:
    ticker: str
    bucket_low: int
    bucket_high: int
    yes_price: float  # in cents
    volume: int


@dataclass
class Opportunity:
    city: str
    date: str
    bucket: str
    market_price: float
    true_prob: float
    edge: float
    forecast: float
    recommendation: str


def fetch_nws_forecast(city: str) -> Optional[Forecast]:
    """Fetch forecast from NWS API."""
    if city not in STATIONS:
        return None
    
    config = STATIONS[city]
    url = f"https://api.weather.gov/gridpoints/{config['gridpoint']}/forecast"
    
    try:
        req = Request(url, headers={"User-Agent": "weather-edge-scanner/1.0"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        
        # Find tomorrow's daytime forecast
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        for period in data.get("properties", {}).get("periods", []):
            if period.get("isDaytime") and tomorrow in period.get("startTime", ""):
                temp = period.get("temperature")
                return Forecast(
                    city=city,
                    date=tomorrow,
                    high_temp=float(temp),
                    confidence="high" if "likely" not in period.get("shortForecast", "").lower() else "medium",
                    source="NWS"
                )
        
        # Fallback to first daytime period
        for period in data.get("properties", {}).get("periods", []):
            if period.get("isDaytime"):
                return Forecast(
                    city=city,
                    date=period.get("startTime", "")[:10],
                    high_temp=float(period.get("temperature")),
                    confidence="medium",
                    source="NWS"
                )
    
    except Exception as e:
        print(f"Warning: Failed to fetch NWS forecast for {city}: {e}")
    
    return None


def normal_cdf(x: float) -> float:
    """Standard normal CDF approximation."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def bucket_probability(forecast_temp: float, bucket_low: int, bucket_high: int, std_dev: float = 2.0) -> float:
    """Calculate probability of temperature falling in bucket."""
    z_low = (bucket_low - forecast_temp) / std_dev
    z_high = (bucket_high - forecast_temp) / std_dev
    return normal_cdf(z_high) - normal_cdf(z_low)


def find_edge(forecast: Forecast, market_prices: list[MarketPrice], min_edge: float = 0.15) -> list[Opportunity]:
    """Find opportunities where market underprices true probability."""
    opportunities = []
    
    # Standard deviation depends on forecast confidence
    std_dev = 2.0 if forecast.confidence == "high" else 2.5 if forecast.confidence == "medium" else 3.0
    
    for price in market_prices:
        true_prob = bucket_probability(forecast.high_temp, price.bucket_low, price.bucket_high, std_dev)
        market_implied = price.yes_price / 100.0
        edge = true_prob - market_implied
        
        if edge >= min_edge:
            # Calculate recommendation
            fair_value = int(true_prob * 100)
            max_buy = int(fair_value * 0.8)  # 20% margin of safety
            
            opportunities.append(Opportunity(
                city=forecast.city,
                date=forecast.date,
                bucket=f"{price.bucket_low}-{price.bucket_high}°F",
                market_price=price.yes_price,
                true_prob=true_prob,
                edge=edge,
                forecast=forecast.high_temp,
                recommendation=f"BUY up to {max_buy}c"
            ))
    
    return sorted(opportunities, key=lambda x: x.edge, reverse=True)


def mock_market_prices(city: str, date: str, center_temp: int) -> list[MarketPrice]:
    """Generate mock market prices for testing (replace with real Kalshi API)."""
    prices = []
    config = STATIONS.get(city, {})
    market = config.get("market", "HIGH")
    
    # Generate buckets around expected temp
    for bucket_low in range(center_temp - 5, center_temp + 5):
        bucket_high = bucket_low + 1
        
        # Mock prices - roughly normal distribution centered below forecast
        distance = abs(bucket_low + 0.5 - center_temp)
        base_price = max(5, int(30 * math.exp(-0.3 * distance)))
        
        prices.append(MarketPrice(
            ticker=f"{market}-{date.replace('-', '')}-T{bucket_low}",
            bucket_low=bucket_low,
            bucket_high=bucket_high,
            yes_price=base_price,
            volume=100
        ))
    
    return prices


def main():
    parser = argparse.ArgumentParser(description="Weather Edge Scanner")
    parser.add_argument("--city", type=str, help="Specific city to scan")
    parser.add_argument("--all", action="store_true", help="Show all opportunities")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--min-edge", type=float, default=0.15, help="Minimum edge threshold")
    args = parser.parse_args()
    
    cities = [args.city] if args.city else list(STATIONS.keys())
    
    all_opportunities = []
    
    if not args.json:
        print("🌡️ Weather Edge Scanner")
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M %Z')}")
        print("=" * 50)
    
    for city in cities:
        if city not in STATIONS:
            print(f"Unknown city: {city}")
            continue
        
        # Fetch forecast
        forecast = fetch_nws_forecast(city)
        if not forecast:
            if not args.json:
                print(f"\n{city.upper()}: No forecast available")
            continue
        
        if not args.json:
            print(f"\n{city.upper()} ({forecast.date})")
            print("━" * 30)
            print(f"NWS Forecast: {forecast.high_temp}°F ({forecast.confidence} confidence)")
        
        # Get market prices (mock for now - replace with Kalshi API)
        prices = mock_market_prices(city, forecast.date, int(forecast.high_temp))
        
        if not args.json:
            print("Current Market Prices:")
            for p in prices:
                marker = " ← EDGE" if bucket_probability(forecast.high_temp, p.bucket_low, p.bucket_high) > (p.yes_price / 100 + 0.15) else ""
                print(f"  {p.bucket_low}-{p.bucket_high}°F: {int(p.yes_price)}c ({int(p.yes_price)}% implied){marker}")
        
        # Find opportunities
        opportunities = find_edge(forecast, prices, args.min_edge)
        all_opportunities.extend(opportunities)
        
        if opportunities and not args.json:
            print(f"\n🎯 OPPORTUNITY: {opportunities[0].bucket} @ {int(opportunities[0].market_price)}c")
            print(f"   NWS says {opportunities[0].forecast}°F → {int(opportunities[0].true_prob * 100)}% true probability")
            print(f"   Edge: +{int(opportunities[0].edge * 100)}%")
            print(f"   {opportunities[0].recommendation}")
        elif not opportunities and not args.json:
            print("\nNo significant edge found.")
    
    if args.json:
        output = [{
            "city": o.city,
            "date": o.date,
            "bucket": o.bucket,
            "market_price": o.market_price,
            "true_probability": round(o.true_prob, 3),
            "edge": round(o.edge, 3),
            "forecast": o.forecast,
            "recommendation": o.recommendation
        } for o in all_opportunities]
        print(json.dumps(output, indent=2))
    
    if not args.json:
        print("\n" + "=" * 50)
        print(f"Total opportunities found: {len(all_opportunities)}")


if __name__ == "__main__":
    main()
