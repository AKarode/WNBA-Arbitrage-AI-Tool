"""
Multi-source odds aggregation and arbitrage detection
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import requests
from datetime import datetime

from core.config.sports_config import SportsConfigManager

load_dotenv()

router = APIRouter(prefix="/api/arbitrage", tags=["arbitrage"])

def calculate_arbitrage_opportunity(odds_data: List[Dict]) -> Dict:
    """Calculate arbitrage opportunities across bookmakers"""
    opportunities = []
    
    for game in odds_data:
        bookmakers = game.get('bookmakers', [])
        if len(bookmakers) < 2:
            continue
            
        # Analyze each market
        for market_type in ['h2h', 'spreads', 'totals']:
            market_odds = {}
            
            # Collect odds from all bookmakers for this market
            for bookmaker in bookmakers:
                for market in bookmaker.get('markets', []):
                    if market.get('key') == market_type:
                        book_name = bookmaker.get('title', 'Unknown')
                        market_odds[book_name] = market.get('outcomes', [])
            
            if len(market_odds) < 2:
                continue
                
            # Find best odds for each outcome
            if market_type == 'h2h':
                arbitrage = find_moneyline_arbitrage(game, market_odds)
                if arbitrage:
                    opportunities.append(arbitrage)
    
    return {
        "opportunities": opportunities,
        "total_opportunities": len(opportunities),
        "timestamp": datetime.utcnow().isoformat()
    }

def find_moneyline_arbitrage(game: Dict, market_odds: Dict) -> Optional[Dict]:
    """Find arbitrage opportunities in moneyline markets"""
    best_odds = {}
    
    # Find best odds for each team
    for book_name, outcomes in market_odds.items():
        for outcome in outcomes:
            team = outcome.get('name')
            price = outcome.get('price', 0)
            
            if team not in best_odds or price > best_odds[team]['price']:
                best_odds[team] = {
                    'price': price,
                    'bookmaker': book_name
                }
    
    if len(best_odds) < 2:
        return None
    
    # Calculate implied probabilities
    implied_probs = []
    total_implied = 0
    
    for team, odds_info in best_odds.items():
        implied_prob = 1 / odds_info['price']
        implied_probs.append(implied_prob)
        total_implied += implied_prob
    
    # Check for arbitrage (total implied probability < 1)
    if total_implied < 1.0:
        profit_margin = (1 - total_implied) * 100
        
        return {
            "game": {
                "home_team": game.get('home_team'),
                "away_team": game.get('away_team'),
                "commence_time": game.get('commence_time'),
                "sport": game.get('sport_title')
            },
            "market_type": "moneyline",
            "arbitrage": {
                "profit_margin": round(profit_margin, 2),
                "total_implied_probability": round(total_implied, 4),
                "best_odds": best_odds,
                "calculation_time": datetime.utcnow().isoformat()
            }
        }
    
    return None

@router.get("/{sport_key}")
async def get_sport_arbitrage(
    sport_key: str,
    min_profit: float = Query(default=1.0, description="Minimum profit margin %"),
    regions: str = Query(default="us", description="Comma-separated regions"),
    markets: str = Query(default="h2h,spreads,totals", description="Markets to analyze")
):
    """Find arbitrage opportunities for a specific sport"""
    
    # Validate sport
    config = SportsConfigManager.get_sport_config(sport_key)
    if not config:
        raise HTTPException(status_code=404, detail=f"Sport '{sport_key}' not supported")
    
    if not config.active:
        raise HTTPException(status_code=400, detail=f"Sport '{sport_key}' is currently inactive")
    
    # Get odds data
    api_key = os.getenv('ODDS_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Odds API key not configured")
    
    try:
        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
        params = {
            'apiKey': api_key,
            'regions': regions,
            'markets': markets,
            'oddsFormat': 'decimal',
            'dateFormat': 'iso'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch odds")
        
        odds_data = response.json()
        arbitrage_analysis = calculate_arbitrage_opportunity(odds_data)
        
        # Filter by minimum profit margin
        filtered_opportunities = [
            opp for opp in arbitrage_analysis['opportunities']
            if opp['arbitrage']['profit_margin'] >= min_profit
        ]
        
        return {
            "sport": {
                "key": sport_key,
                "title": config.title,
                "min_profit_threshold": min_profit
            },
            "analysis": {
                "total_games_analyzed": len(odds_data),
                "opportunities_found": len(filtered_opportunities),
                "filtered_opportunities": filtered_opportunities,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

@router.get("/")
async def get_all_arbitrage_opportunities(
    min_profit: float = Query(default=1.0, description="Minimum profit margin %"),
    limit_sports: int = Query(default=3, description="Max sports to analyze")
):
    """Find arbitrage opportunities across all active sports"""
    
    active_sports = SportsConfigManager.get_active_sports()[:limit_sports]
    api_key = os.getenv('ODDS_API_KEY')
    
    if not api_key:
        raise HTTPException(status_code=500, detail="Odds API key not configured")
    
    all_opportunities = []
    analysis_summary = {}
    
    for config in active_sports:
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{config.key}/odds"
            params = {
                'apiKey': api_key,
                'regions': 'us',
                'markets': 'h2h,spreads,totals',
                'oddsFormat': 'decimal',
                'dateFormat': 'iso'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                odds_data = response.json()
                arbitrage_analysis = calculate_arbitrage_opportunity(odds_data)
                
                sport_opportunities = [
                    opp for opp in arbitrage_analysis['opportunities']
                    if opp['arbitrage']['profit_margin'] >= min_profit
                ]
                
                all_opportunities.extend(sport_opportunities)
                analysis_summary[config.key] = {
                    "sport_title": config.title,
                    "games_analyzed": len(odds_data),
                    "opportunities_found": len(sport_opportunities)
                }
            else:
                analysis_summary[config.key] = {
                    "sport_title": config.title,
                    "error": f"API error: {response.status_code}",
                    "games_analyzed": 0,
                    "opportunities_found": 0
                }
                
        except Exception as e:
            analysis_summary[config.key] = {
                "sport_title": config.title,
                "error": str(e),
                "games_analyzed": 0,
                "opportunities_found": 0
            }
    
    # Sort opportunities by profit margin (highest first)
    all_opportunities.sort(
        key=lambda x: x['arbitrage']['profit_margin'], 
        reverse=True
    )
    
    return {
        "analysis_summary": analysis_summary,
        "arbitrage_opportunities": all_opportunities,
        "total_opportunities": len(all_opportunities),
        "sports_analyzed": len(analysis_summary),
        "min_profit_threshold": min_profit,
        "analysis_timestamp": datetime.utcnow().isoformat()
    }