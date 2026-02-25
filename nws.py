#!/usr/bin/env python3
"""
NWS API Client - Fetch weather forecasts from National Weather Service
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from urllib.request import urlopen, Request

# NWS gridpoint coordinates for major cities
GRIDPOINTS = {
    "miami": "MFL/110,50",
    "chicago": "LOT/76,73",
    "nyc": "OKX/33,37",
    "la": "LOX/154,44",
    "austin": "EWX/156,91",
    "denver": "BOU/62,60",
    "seattle": "SEW/124,67",
    "boston": "BOX/71,90",
    "phoenix": "PSR/161,58",
    "atlanta": "FFC/52,87",
}

USER_AGENT = "weather-edge-scanner/1.0 (github.com/blainerdavis-commits/weather-edge)"


@dataclass
class NWSForecast:
    city: str
    date: str
    high_temp: float
    low_temp: Optional[float]
    short_forecast: str
    detailed_forecast: str
    wind_speed: str
    precipitation_prob: Optional[int]


def get_gridpoint(city: str) -> Optional[str]:
    """Get NWS gridpoint for a city."""
    return GRIDPOINTS.get(city.lower())


def fetch_forecast(city: str, days_ahead: int = 1) -> Optional[NWSForecast]:
    """
    Fetch forecast from NWS API.
    
    Args:
        city: City name (must be in GRIDPOINTS)
        days_ahead: Number of days ahead (1 = tomorrow)
    
    Returns:
        NWSForecast or None if fetch fails
    """
    gridpoint = get_gridpoint(city)
    if not gridpoint:
        raise ValueError(f"Unknown city: {city}. Available: {list(GRIDPOINTS.keys())}")
    
    url = f"https://api.weather.gov/gridpoints/{gridpoint}/forecast"
    
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"Error fetching forecast: {e}")
        return None
    
    # Calculate target date
    target_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    
    # Find matching daytime period
    periods = data.get("properties", {}).get("periods", [])
    
    for period in periods:
        period_date = period.get("startTime", "")[:10]
        is_daytime = period.get("isDaytime", False)
        
        if period_date == target_date and is_daytime:
            return NWSForecast(
                city=city,
                date=target_date,
                high_temp=float(period.get("temperature", 0)),
                low_temp=None,  # Would need to find matching nighttime period
                short_forecast=period.get("shortForecast", ""),
                detailed_forecast=period.get("detailedForecast", ""),
                wind_speed=period.get("windSpeed", ""),
                precipitation_prob=period.get("probabilityOfPrecipitation", {}).get("value")
            )
    
    # Fallback to first daytime period if target not found
    for period in periods:
        if period.get("isDaytime", False):
            return NWSForecast(
                city=city,
                date=period.get("startTime", "")[:10],
                high_temp=float(period.get("temperature", 0)),
                low_temp=None,
                short_forecast=period.get("shortForecast", ""),
                detailed_forecast=period.get("detailedForecast", ""),
                wind_speed=period.get("windSpeed", ""),
                precipitation_prob=period.get("probabilityOfPrecipitation", {}).get("value")
            )
    
    return None


def fetch_hourly(city: str) -> list[dict]:
    """Fetch hourly forecast for more precise temperature predictions."""
    gridpoint = get_gridpoint(city)
    if not gridpoint:
        return []
    
    url = f"https://api.weather.gov/gridpoints/{gridpoint}/forecast/hourly"
    
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        return data.get("properties", {}).get("periods", [])
    except Exception:
        return []


if __name__ == "__main__":
    # Test
    import sys
    city = sys.argv[1] if len(sys.argv) > 1 else "miami"
    
    forecast = fetch_forecast(city)
    if forecast:
        print(f"Forecast for {forecast.city} on {forecast.date}:")
        print(f"  High: {forecast.high_temp}°F")
        print(f"  Conditions: {forecast.short_forecast}")
        print(f"  Wind: {forecast.wind_speed}")
        if forecast.precipitation_prob is not None:
            print(f"  Precipitation: {forecast.precipitation_prob}%")
    else:
        print(f"Could not fetch forecast for {city}")
