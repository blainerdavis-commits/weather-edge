#!/usr/bin/env python3
"""
Weather Edge v2 - Multi-Model Consensus Edge Detection
Combines NWS + Open-Meteo ensemble models for weather betting edge

Edge Criteria:
1. Models AGREE (low spread) + Market diverges = EDGE
2. Models DISAGREE (high spread) = SKIP (uncertainty)
3. Current temps running hot/cold vs forecast = UPDATE EDGE
"""

import os
import sys
import json
import math
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, asdict, field

# =============================================================================
# STATION MAPPING - Kalshi uses specific measurement stations
# =============================================================================

STATIONS = {
    'chicago': {
        'name': 'Chicago',
        'station': 'KMDW',  # Midway - Kalshi uses this, NOT O'Hare
        'nws_grid': ('LOT', 75, 71),  # Grid for Midway area
        'lat': 41.785,
        'lon': -87.752,
        'obs_station': 'KMDW',  # METAR station
    },
    'miami': {
        'name': 'Miami',
        'station': 'KMIA',
        'nws_grid': ('MFL', 110, 50),
        'lat': 25.795,
        'lon': -80.287,
        'obs_station': 'KMIA',
    },
    'nyc': {
        'name': 'NYC',
        'station': 'NYC',  # Central Park - special case
        'nws_grid': ('OKX', 33, 37),
        'lat': 40.7829,  # Central Park
        'lon': -73.9654,
        'obs_station': 'KNYC',  # Central Park automated
    },
    'austin': {
        'name': 'Austin',
        'station': 'KAUS',
        'nws_grid': ('EWX', 111, 93),
        'lat': 30.1945,
        'lon': -97.6699,
        'obs_station': 'KAUS',
    },
    'denver': {
        'name': 'Denver',
        'station': 'KDEN',
        'nws_grid': ('BOU', 62, 60),
        'lat': 39.8561,
        'lon': -104.6737,
        'obs_station': 'KDEN',
    },
    'la': {
        'name': 'Los Angeles',
        'station': 'KLAX',
        'nws_grid': ('LOX', 154, 44),
        'lat': 33.9416,
        'lon': -118.4085,
        'obs_station': 'KLAX',
    },
}

# Kalshi series tickers (from API discovery)
KALSHI_SERIES = {
    'chicago': 'KXHIGHCHI',
    'miami': 'KXHIGHMIA',
    'nyc': 'KXHIGHNY',  # Note: no 'C' in NYC
    'austin': 'KXHIGHAUS',
    'denver': 'KXHIGHDEN',
    'la': 'KXHIGHLAX',
}

# Legacy city codes (for backwards compatibility)
KALSHI_CODES = {
    'chicago': 'CHI',
    'miami': 'MIA',
    'nyc': 'NYC',
    'austin': 'AUS',
    'denver': 'DEN',
    'la': 'LA',
}

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ModelForecast:
    """Single model forecast"""
    model: str
    high_temp: float
    low_temp: float = None
    source: str = ''
    fetched_at: str = ''

@dataclass
class ConsensusData:
    """Multi-model consensus analysis"""
    forecasts: List[ModelForecast]
    consensus_high: float  # Average of all models
    spread: float  # Max - Min (disagreement)
    std_dev: float  # Standard deviation
    min_forecast: float
    max_forecast: float
    model_count: int
    agreement_level: str  # 'strong', 'moderate', 'weak', 'divergent'
    
    def to_dict(self):
        return {
            'forecasts': [asdict(f) for f in self.forecasts],
            'consensus_high': self.consensus_high,
            'spread': self.spread,
            'std_dev': self.std_dev,
            'min_forecast': self.min_forecast,
            'max_forecast': self.max_forecast,
            'model_count': self.model_count,
            'agreement_level': self.agreement_level,
        }

@dataclass
class EdgeOpportunity:
    """Trading opportunity with edge analysis"""
    ticker: str
    city: str
    date: str
    threshold: float
    consensus_high: float
    market_price: float
    model_probability: float
    edge_pct: float
    confidence: str  # 'high', 'medium', 'low'
    recommendation: str  # 'strong_buy', 'buy', 'skip', 'avoid'
    model_spread: float
    agreement: str = 'DIVERGENT'  # 'STRONG', 'MODERATE', 'WEAK', 'DIVERGENT'
    notes: List[str] = field(default_factory=list)

# =============================================================================
# OPEN-METEO MULTI-MODEL FETCHER
# =============================================================================

def fetch_open_meteo_models(lat: float, lon: float, date: str) -> List[ModelForecast]:
    """
    Fetch forecasts from multiple models via Open-Meteo
    
    Models available:
    - ecmwf_ifs04: European model (generally most accurate)
    - gfs_seamless: US GFS model
    - icon_seamless: German ICON model
    - gem_seamless: Canadian GEM model
    """
    base_url = "https://api.open-meteo.com/v1/forecast"
    
    # Models to fetch
    models = ['ecmwf_ifs04', 'gfs_seamless', 'icon_seamless', 'gem_seamless']
    
    forecasts = []
    
    for model in models:
        try:
            params = {
                'latitude': lat,
                'longitude': lon,
                'daily': 'temperature_2m_max,temperature_2m_min',
                'models': model,
                'temperature_unit': 'fahrenheit',
                'timezone': 'America/New_York',
                'start_date': date,
                'end_date': date,
            }
            
            resp = requests.get(base_url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            daily = data.get('daily', {})
            dates = daily.get('time', [])
            highs = daily.get('temperature_2m_max', [])
            lows = daily.get('temperature_2m_min', [])
            
            if dates and highs and date in dates:
                idx = dates.index(date)
                high_val = highs[idx]
                low_val = lows[idx] if lows and idx < len(lows) else None
                
                # Skip if no data
                if high_val is None:
                    print(f"  ⚠️  {model}: No forecast data for {date}")
                    continue
                
                forecasts.append(ModelForecast(
                    model=model.upper().replace('_', ' '),
                    high_temp=round(high_val, 1),
                    low_temp=round(low_val, 1) if low_val is not None else None,
                    source='open-meteo',
                    fetched_at=datetime.now().isoformat(),
                ))
        except Exception as e:
            print(f"  ⚠️  {model}: {e}")
    
    return forecasts

# =============================================================================
# NWS FETCHER
# =============================================================================

def fetch_nws_forecast(city: str, date: str) -> Optional[ModelForecast]:
    """Fetch NWS forecast for a city"""
    if city not in STATIONS:
        return None
    
    station = STATIONS[city]
    office, x, y = station['nws_grid']
    url = f"https://api.weather.gov/gridpoints/{office}/{x},{y}/forecast/hourly"
    
    headers = {
        'User-Agent': '(kalshi-edge-v2, weather@example.com)',
        'Accept': 'application/geo+json'
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        periods = data.get('properties', {}).get('periods', [])
        
        # Find all temps for target date
        day_temps = []
        for period in periods:
            start_time = period.get('startTime', '')
            if date in start_time:
                temp = period.get('temperature')
                if temp is not None:
                    day_temps.append(temp)
        
        if not day_temps:
            return None
        
        return ModelForecast(
            model='NWS',
            high_temp=max(day_temps),
            low_temp=min(day_temps),
            source='api.weather.gov',
            fetched_at=datetime.now().isoformat(),
        )
    except Exception as e:
        print(f"  ⚠️  NWS: {e}")
        return None

# =============================================================================
# CURRENT OBSERVATIONS (Real-Time Monitoring)
# =============================================================================

def get_current_temp(city: str) -> Optional[Dict]:
    """
    Fetch current temperature from METAR observations
    Used for real-time edge adjustments
    """
    if city not in STATIONS:
        return None
    
    station = STATIONS[city]['obs_station']
    
    # Aviation Weather Center METAR API
    url = f"https://aviationweather.gov/api/data/metar?ids={station}&format=json"
    
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        if not data:
            return None
        
        obs = data[0]
        temp_c = obs.get('temp')
        
        if temp_c is None:
            return None
        
        temp_f = round(temp_c * 9/5 + 32, 1)
        
        return {
            'station': station,
            'temp_f': temp_f,
            'temp_c': temp_c,
            'obs_time': obs.get('obsTime', ''),
            'raw_metar': obs.get('rawOb', ''),
        }
    except Exception as e:
        print(f"  ⚠️  Current obs error: {e}")
        return None

# =============================================================================
# CONSENSUS CALCULATOR
# =============================================================================

def calculate_consensus(forecasts: List[ModelForecast]) -> Optional[ConsensusData]:
    """
    Calculate model consensus and agreement level
    
    Agreement Levels:
    - strong: spread <= 2°F (all models agree closely)
    - moderate: spread 2-4°F (general agreement)
    - weak: spread 4-6°F (some disagreement)
    - divergent: spread > 6°F (significant uncertainty)
    """
    if not forecasts or len(forecasts) < 2:
        return None
    
    highs = [f.high_temp for f in forecasts]
    
    consensus_high = round(sum(highs) / len(highs), 1)
    min_forecast = min(highs)
    max_forecast = max(highs)
    spread = round(max_forecast - min_forecast, 1)
    
    # Standard deviation
    variance = sum((h - consensus_high) ** 2 for h in highs) / len(highs)
    std_dev = round(math.sqrt(variance), 2)
    
    # Determine agreement level
    if spread <= 2:
        agreement = 'strong'
    elif spread <= 4:
        agreement = 'moderate'
    elif spread <= 6:
        agreement = 'weak'
    else:
        agreement = 'divergent'
    
    return ConsensusData(
        forecasts=forecasts,
        consensus_high=consensus_high,
        spread=spread,
        std_dev=std_dev,
        min_forecast=min_forecast,
        max_forecast=max_forecast,
        model_count=len(forecasts),
        agreement_level=agreement,
    )

# =============================================================================
# PROBABILITY ESTIMATION
# =============================================================================

def get_city_bias(city: str = None) -> float:
    """Get empirical bias correction for a city from bias_model_v2.json"""
    try:
        bias_model = load_bias_model()
        empirical = bias_model.get('empirical_bias', {})
        if city and city.lower() in empirical.get('by_city', {}):
            return empirical['by_city'][city.lower()].get('bias', 2.0)
        return empirical.get('default_warm_bias', 2.0)
    except Exception:
        return 2.0  # Default fallback


def estimate_probability(consensus: ConsensusData, threshold: float, bias_correction: float = None, city: str = None) -> Tuple[float, str]:
    """
    Estimate probability that actual temp >= threshold
    
    Uses consensus and spread to determine confidence
    
    Args:
        consensus: Multi-model consensus data
        threshold: Temperature threshold to estimate probability for
        bias_correction: Degrees to add to forecast (None = load from bias model)
        city: City name for city-specific bias lookup
    """
    # CRITICAL: Validate consensus data before calculating
    if consensus is None or consensus.consensus_high == 0 or consensus.model_count < 2:
        return 0.0, 'invalid'  # Return zero probability for invalid data
    
    # Get bias correction from model or use provided value
    if bias_correction is None:
        bias_correction = get_city_bias(city)
    
    # Apply bias correction - models consistently underforecast highs
    corrected_consensus = consensus.consensus_high + bias_correction
    diff = corrected_consensus - threshold
    
    # Base probability using logistic function
    # Steeper curve when models agree, flatter when they diverge
    if consensus.agreement_level == 'strong':
        steepness = 0.7  # More confident
    elif consensus.agreement_level == 'moderate':
        steepness = 0.5
    elif consensus.agreement_level == 'weak':
        steepness = 0.35
    else:  # divergent
        steepness = 0.25  # Very uncertain
    
    prob = 1 / (1 + math.exp(-steepness * diff))
    
    # Cap probabilities based on uncertainty
    if consensus.agreement_level == 'divergent':
        prob = max(0.15, min(0.85, prob))  # Never too confident
    elif consensus.agreement_level == 'weak':
        prob = max(0.10, min(0.90, prob))
    
    # Confidence level
    if consensus.agreement_level in ['strong', 'moderate'] and abs(diff) >= 3:
        confidence = 'high'
    elif consensus.agreement_level == 'strong' or abs(diff) >= 5:
        confidence = 'medium'
    else:
        confidence = 'low'
    
    return round(prob, 3), confidence

# =============================================================================
# KALSHI MARKET FETCHER (RSA Auth)
# =============================================================================

def get_kalshi_client():
    """Get authenticated Kalshi client"""
    try:
        from kalshi_auth import get_client
        return get_client()
    except Exception as e:
        print(f"  ⚠️  Kalshi client error: {e}")
        return None

def get_weather_markets(client, city: str, date: str) -> List[dict]:
    """Fetch Kalshi weather markets for city/date using event-based lookup"""
    series_ticker = KALSHI_SERIES.get(city)
    if not series_ticker:
        print(f"  ⚠️  No Kalshi series for city: {city}")
        return []
    
    # Format: KXHIGHCHI-26MAR06 (YY at end, not YYMMDD)
    dt = datetime.strptime(date, '%Y-%m-%d')
    date_str = dt.strftime('%y%b%d').upper()  # e.g., 26MAR06
    
    event_ticker = f"{series_ticker}-{date_str}"
    
    try:
        # Use the raw client methods to fetch by event
        from kalshi_auth import get_headers, load_private_key, API_BASE
        import requests
        
        pk = load_private_key()
        path = '/trade-api/v2/markets'
        params = {'event_ticker': event_ticker, 'limit': 50}
        query = '&'.join(f'{k}={v}' for k, v in params.items())
        headers = get_headers(pk, 'GET', f'{path}?{query}')
        
        resp = requests.get(API_BASE + path, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        markets = resp.json().get('markets', [])
        return markets
    except Exception as e:
        print(f"  ⚠️  Markets fetch error: {e}")
        return []

def parse_temp_threshold(ticker: str) -> Optional[Tuple[float, str]]:
    """
    Extract temperature threshold from ticker
    
    Formats:
    - KXHIGHCHI-26MAR06-B75.5 → (75.5, 'above') - Will it be >= 75.5?
    - KXHIGHCHI-26MAR06-T76 → (76.0, 'above') - Will it be >= 76?
    
    Returns: (threshold, direction) or None
    """
    try:
        # Format: TICKER-DATE-[B|T]VALUE
        parts = ticker.split('-')
        if len(parts) >= 3:
            threshold_part = parts[-1]  # e.g., "B75.5" or "T76"
            
            if threshold_part.startswith('B'):
                return (float(threshold_part[1:]), 'above')
            elif threshold_part.startswith('T'):
                return (float(threshold_part[1:]), 'above')
    except:
        pass
    return None

# =============================================================================
# EDGE ANALYSIS ENGINE
# =============================================================================

def analyze_edge(city: str, date: str, min_edge: float = 0.08) -> Dict:
    """
    Main edge analysis function
    
    Returns comprehensive analysis with:
    - All model forecasts
    - Consensus data
    - Market prices
    - Edge opportunities
    - Recommendation
    """
    print(f"\n{'='*60}")
    print(f"🔍 EDGE ANALYSIS: {city.upper()} - {date}")
    print(f"{'='*60}")
    
    if city not in STATIONS:
        return {'error': f'Unknown city: {city}'}
    
    station = STATIONS[city]
    
    # Step 1: Fetch all model forecasts
    print(f"\n📡 Fetching forecasts for {station['name']} ({station['station']})...")
    
    forecasts = []
    
    # NWS
    nws = fetch_nws_forecast(city, date)
    if nws:
        forecasts.append(nws)
        print(f"  ✅ NWS: {nws.high_temp}°F")
    
    # Open-Meteo models
    om_forecasts = fetch_open_meteo_models(station['lat'], station['lon'], date)
    for f in om_forecasts:
        forecasts.append(f)
        print(f"  ✅ {f.model}: {f.high_temp}°F")
    
    if len(forecasts) < 2:
        return {'error': 'Insufficient forecast data', 'forecasts': forecasts}
    
    # Step 2: Calculate consensus
    print(f"\n📊 Calculating consensus...")
    consensus = calculate_consensus(forecasts)
    
    print(f"  Consensus High: {consensus.consensus_high}°F")
    print(f"  Model Spread: {consensus.spread}°F")
    print(f"  Std Dev: {consensus.std_dev}°F")
    print(f"  Agreement: {consensus.agreement_level.upper()}")
    
    # Step 3: Get current temperature (real-time adjustment)
    current = get_current_temp(city)
    if current:
        print(f"\n🌡️  Current Temp: {current['temp_f']}°F @ {current['station']}")
    
    # Step 4: Fetch Kalshi markets
    print(f"\n💰 Fetching Kalshi markets...")
    client = get_kalshi_client()
    
    markets = []
    opportunities = []
    
    if client:
        markets = get_weather_markets(client, city, date)
        print(f"  Found {len(markets)} markets")
        
        # Analyze each market
        for market in markets:
            ticker = market['ticker']
            parsed = parse_temp_threshold(ticker)
            
            if parsed is None:
                continue
            
            threshold, direction = parsed
            
            # Get price - Kalshi uses cents (0-100 scale)
            yes_ask = market.get('yes_ask') or market.get('last_price') or 0
            
            # Convert from cents to decimal if needed
            if yes_ask > 1:
                yes_price = yes_ask / 100  # Convert cents to decimal
            else:
                yes_price = yes_ask
            
            if yes_price <= 0 or yes_price >= 1:
                continue
            
            # Estimate probability (with city-specific bias correction)
            model_prob, confidence = estimate_probability(consensus, threshold, city=city)
            
            # Calculate edge
            edge = model_prob - yes_price
            edge_pct = round(edge * 100, 1)
            
            # Determine recommendation
            notes = []
            
            if consensus.agreement_level == 'divergent':
                recommendation = 'skip'
                notes.append('Models strongly disagree - high uncertainty')
            elif consensus.agreement_level == 'weak' and abs(edge) < 0.15:
                recommendation = 'skip'
                notes.append('Weak model agreement, edge not large enough')
            elif edge >= 0.15 and consensus.agreement_level in ['strong', 'moderate']:
                recommendation = 'strong_buy'
                notes.append('Strong edge with model consensus')
            elif edge >= min_edge and consensus.agreement_level in ['strong', 'moderate']:
                recommendation = 'buy'
                notes.append('Positive edge with model support')
            elif edge < -0.15:
                recommendation = 'avoid'
                notes.append('Market overpriced vs models')
            else:
                recommendation = 'skip'
                notes.append('Insufficient edge')
            
            # Add current temp context
            if current:
                hour = datetime.now().hour
                if hour >= 10 and hour <= 14:  # Mid-day check
                    expected_at_this_hour = consensus.consensus_high - (14 - hour) * 1.5
                    actual_diff = current['temp_f'] - expected_at_this_hour
                    if actual_diff >= 3:
                        notes.append(f'Running HOT: +{actual_diff:.1f}°F vs expected')
                    elif actual_diff <= -3:
                        notes.append(f'Running COLD: {actual_diff:.1f}°F vs expected')
            
            opp = EdgeOpportunity(
                ticker=ticker,
                city=city,
                date=date,
                threshold=threshold,
                consensus_high=consensus.consensus_high,
                market_price=yes_price,
                model_probability=model_prob,
                edge_pct=edge_pct,
                confidence=confidence,
                recommendation=recommendation,
                model_spread=consensus.spread,
                agreement=consensus.agreement_level.upper(),
                notes=notes,
            )
            opportunities.append(opp)
    else:
        print("  ⚠️  No Kalshi client - skipping market analysis")
    
    # Sort opportunities by edge
    opportunities.sort(key=lambda x: x.edge_pct, reverse=True)
    
    # Build result
    result = {
        'city': city,
        'date': date,
        'station': station['station'],
        'consensus': consensus.to_dict(),
        'current_temp': current,
        'opportunities': [asdict(o) for o in opportunities],
        'edge_found': any(o.recommendation in ['buy', 'strong_buy'] for o in opportunities),
        'analyzed_at': datetime.now().isoformat(),
    }
    
    return result

# =============================================================================
# PRETTY PRINTING
# =============================================================================

def print_analysis(result: Dict):
    """Pretty print analysis results"""
    if 'error' in result:
        print(f"\n❌ Error: {result['error']}")
        return
    
    consensus = result['consensus']
    opportunities = result['opportunities']
    
    # Model comparison table
    print(f"\n📊 MODEL COMPARISON:")
    print(f"{'─'*50}")
    for f in consensus['forecasts']:
        print(f"  {f['model']:20s} │ {f['high_temp']:5.1f}°F")
    print(f"{'─'*50}")
    print(f"  {'CONSENSUS':20s} │ {consensus['consensus_high']:5.1f}°F")
    print(f"  {'Spread':20s} │ {consensus['spread']:5.1f}°F")
    print(f"  {'Agreement':20s} │ {consensus['agreement_level'].upper()}")
    
    if result.get('current_temp'):
        ct = result['current_temp']
        print(f"\n🌡️  CURRENT: {ct['temp_f']}°F @ {ct['station']}")
    
    # Opportunities
    if opportunities:
        print(f"\n💰 MARKET ANALYSIS:")
        print(f"{'─'*70}")
        
        buys = [o for o in opportunities if o['recommendation'] in ['buy', 'strong_buy']]
        skips = [o for o in opportunities if o['recommendation'] == 'skip']
        
        if buys:
            print(f"\n✅ EDGE FOUND - {len(buys)} opportunity(ies):\n")
            for opp in buys:
                emoji = '🔥' if opp['recommendation'] == 'strong_buy' else '✅'
                print(f"  {emoji} {opp['ticker']}")
                print(f"     Threshold: >= {opp['threshold']}°F")
                print(f"     Consensus: {opp['consensus_high']}°F | Market: {opp['market_price']:.0%} | Model: {opp['model_probability']:.0%}")
                print(f"     EDGE: +{opp['edge_pct']:.1f}% | Confidence: {opp['confidence'].upper()}")
                for note in opp['notes']:
                    print(f"     → {note}")
                print()
        else:
            print(f"\n❌ NO EDGE TODAY")
            if consensus['agreement_level'] == 'divergent':
                print(f"   Reason: Models strongly disagree (spread: {consensus['spread']}°F)")
            else:
                print(f"   Reason: Market prices align with model consensus")
    
    print(f"{'─'*70}")

# =============================================================================
# BIAS MODEL TRACKING
# =============================================================================

def load_bias_model() -> Dict:
    """Load historical bias data"""
    path = os.path.join(os.path.dirname(__file__), 'bias_model_v2.json')
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {'stations': {}, 'models': {}, 'history': []}

def save_bias_model(data: Dict):
    """Save bias model"""
    path = os.path.join(os.path.dirname(__file__), 'bias_model_v2.json')
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def record_settlement(city: str, date: str, actual_high: float, forecasts: List[Dict]):
    """
    Record actual settlement for bias tracking
    
    Call this after market settles to update model accuracy
    """
    bias_data = load_bias_model()
    
    errors = []
    for f in forecasts:
        model = f['model']
        forecast_high = f['high_temp']
        error = actual_high - forecast_high
        
        if model not in bias_data['models']:
            bias_data['models'][model] = {
                'total_forecasts': 0,
                'total_error': 0,
                'abs_error_sum': 0,
                'errors': []
            }
        
        m = bias_data['models'][model]
        m['total_forecasts'] += 1
        m['total_error'] += error
        m['abs_error_sum'] += abs(error)
        m['errors'].append(error)
        m['mean_bias'] = round(m['total_error'] / m['total_forecasts'], 2)
        m['mae'] = round(m['abs_error_sum'] / m['total_forecasts'], 2)
        
        errors.append({'model': model, 'forecast': forecast_high, 'error': error})
    
    # Record history
    bias_data['history'].append({
        'city': city,
        'date': date,
        'actual_high': actual_high,
        'errors': errors,
        'recorded_at': datetime.now().isoformat(),
    })
    
    save_bias_model(bias_data)
    print(f"✅ Settlement recorded: {city} {date} = {actual_high}°F")

# =============================================================================
# MAIN SCANNER
# =============================================================================

def scan_all_cities(date: str = None, cities: List[str] = None) -> Dict:
    """
    Scan all cities for edge opportunities
    """
    if date is None:
        tomorrow = datetime.now() + timedelta(days=1)
        date = tomorrow.strftime('%Y-%m-%d')
    
    if cities is None:
        cities = ['chicago', 'miami', 'nyc', 'austin']
    
    results = {}
    all_opportunities = []
    
    for city in cities:
        result = analyze_edge(city, date)
        results[city] = result
        print_analysis(result)
        
        if 'opportunities' in result:
            for opp in result['opportunities']:
                opp['city'] = city
                all_opportunities.append(opp)
    
    # Summary
    buys = [o for o in all_opportunities if o['recommendation'] in ['buy', 'strong_buy']]
    
    print(f"\n{'='*60}")
    print(f"📋 SUMMARY - {date}")
    print(f"{'='*60}")
    
    if buys:
        print(f"\n🎯 EDGE FOUND: {len(buys)} opportunity(ies)")
        for opp in sorted(buys, key=lambda x: x['edge_pct'], reverse=True):
            emoji = '🔥' if opp['recommendation'] == 'strong_buy' else '✅'
            print(f"  {emoji} {opp['city'].upper()}: {opp['ticker']} → +{opp['edge_pct']:.1f}% edge")
    else:
        print(f"\n❌ NO EDGE TODAY")
        print(f"   Models and markets aligned, or high uncertainty")
    
    print(f"\n{'='*60}\n")
    
    return {
        'date': date,
        'cities': results,
        'total_opportunities': len(buys),
        'opportunities': buys,
    }

# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Weather Edge v2 - Multi-Model Consensus Scanner')
    parser.add_argument('--city', default=None, help='Single city to scan (default: all)')
    parser.add_argument('--date', default=None, help='Date YYYY-MM-DD (default: tomorrow)')
    parser.add_argument('--today', action='store_true', help='Scan today instead of tomorrow')
    parser.add_argument('--min-edge', type=float, default=0.08, help='Minimum edge threshold')
    parser.add_argument('--json', action='store_true', help='Output JSON')
    
    args = parser.parse_args()
    
    # Determine date
    if args.today:
        date = datetime.now().strftime('%Y-%m-%d')
    elif args.date:
        date = args.date
    else:
        tomorrow = datetime.now() + timedelta(days=1)
        date = tomorrow.strftime('%Y-%m-%d')
    
    # Scan
    if args.city:
        result = analyze_edge(args.city, date, args.min_edge)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print_analysis(result)
    else:
        results = scan_all_cities(date)
        if args.json:
            print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
