#!/usr/bin/env python3
"""
Kelly Criterion Calculator for Kalshi Trading
Based on the Trading Bible (adapted from @noisyb0y1)
"""

import sys

def calculate_ev(p_true: float, market_price: float) -> float:
    """Calculate Expected Value (edge)"""
    return p_true - market_price

def calculate_kelly(p_true: float, market_price: float) -> float:
    """
    Calculate Kelly fraction for Kalshi YES bet
    
    f = (p * b - q) / b
    where b = (1 - price) / price for YES bets
    """
    if market_price <= 0 or market_price >= 1:
        return 0
    
    q = 1 - p_true
    b = (1 - market_price) / market_price  # odds ratio
    
    kelly = (p_true * b - q) / b
    return max(0, kelly)  # never negative

def calculate_bet_size(bankroll: float, p_true: float, market_price: float, 
                       half_kelly: bool = True, max_exposure: float = 0.20) -> dict:
    """
    Calculate recommended bet size
    
    Returns dict with all calculations
    """
    ev = calculate_ev(p_true, market_price)
    kelly_fraction = calculate_kelly(p_true, market_price)
    
    # Apply half-Kelly for safety
    if half_kelly:
        kelly_fraction = kelly_fraction / 2
    
    # Calculate dollar amount
    bet_dollars = bankroll * kelly_fraction
    
    # Cap at max exposure
    max_bet = bankroll * max_exposure
    if bet_dollars > max_bet:
        bet_dollars = max_bet
        kelly_fraction = max_exposure
    
    # Calculate contracts at this price
    contracts = int(bet_dollars / market_price)
    actual_cost = contracts * market_price
    potential_profit = contracts * (1 - market_price)
    
    return {
        'ev': ev,
        'edge_pct': ev * 100,
        'kelly_fraction': kelly_fraction,
        'kelly_pct': kelly_fraction * 100,
        'bet_dollars': bet_dollars,
        'contracts': contracts,
        'actual_cost': actual_cost,
        'potential_profit': potential_profit,
        'has_edge': ev > 0,
        'strong_edge': ev > 0.10,
    }

def print_analysis(bankroll: float, p_true: float, market_price: float):
    """Print full trade analysis"""
    result = calculate_bet_size(bankroll, p_true, market_price)
    
    print("\n" + "="*50)
    print("TRADE ANALYSIS")
    print("="*50)
    print(f"Your probability (p_true):  {p_true:.0%}")
    print(f"Market price:               ${market_price:.2f} ({market_price:.0%})")
    print(f"Bankroll:                   ${bankroll:,.2f}")
    print("-"*50)
    print(f"Expected Value (EV):        {result['ev']:.2f} ({result['edge_pct']:.1f}%)")
    print(f"Kelly Fraction (half):      {result['kelly_pct']:.1f}%")
    print("-"*50)
    
    if not result['has_edge']:
        print("❌ NO EDGE - DO NOT TRADE")
    elif not result['strong_edge']:
        print("⚠️  WEAK EDGE (<10%) - PROCEED WITH CAUTION")
    else:
        print("✅ STRONG EDGE - TRADE APPROVED")
        print(f"\nRECOMMENDED:")
        print(f"  Bet size:          ${result['bet_dollars']:,.2f}")
        print(f"  Contracts:         {result['contracts']:,}")
        print(f"  Actual cost:       ${result['actual_cost']:,.2f}")
        print(f"  Potential profit:  ${result['potential_profit']:,.2f}")
    
    print("="*50 + "\n")
    return result

if __name__ == "__main__":
    if len(sys.argv) == 4:
        bankroll = float(sys.argv[1])
        p_true = float(sys.argv[2])
        market_price = float(sys.argv[3])
    else:
        # Default example: our Chicago bet
        print("Usage: python kelly.py <bankroll> <p_true> <market_price>")
        print("Example: python kelly.py 38699 0.70 0.27")
        print("\nRunning with example values...")
        bankroll = 38699  # Current cash balance
        p_true = 0.70     # 70% confident
        market_price = 0.27  # 27 cents
    
    print_analysis(bankroll, p_true, market_price)
