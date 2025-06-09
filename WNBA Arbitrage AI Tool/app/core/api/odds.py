"""
Multi-sport odds API endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import os
from dotenv import load_dotenv
import requests

from core.config.sports_config import SportsConfigManager

load_dotenv()

router = APIRouter(prefix="/api/odds", tags=["odds"])

@router.get("/sports")
async def get_supported_sports():
    """Get all supported sports"""
    sports = SportsConfigManager.get_all_sports()
    return {
        "sports": [
            {
                "key": config.key,
                "title": config.title, 
                "active": config.active,
                "markets": config.markets,
                "min_profit_margin": config.min_profit_margin
            }
            for config in sports.values()
        ],
        "total": len(sports)
    }

@router.get("/{sport_key}")
async def get_sport_odds(
    sport_key: str,
    regions: str = Query(default="us", description="Comma-separated regions"),
    markets: str = Query(default="h2h", description="Comma-separated markets"),
    odds_format: str = Query(default="decimal", description="Odds format")
):
    """Get odds for a specific sport"""
    
    # Validate sport
    config = SportsConfigManager.get_sport_config(sport_key)
    if not config:
        raise HTTPException(status_code=404, detail=f"Sport '{sport_key}' not supported")
    
    if not config.active:
        raise HTTPException(status_code=400, detail=f"Sport '{sport_key}' is currently inactive")
    
    # Get API key
    api_key = os.getenv('ODDS_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Odds API key not configured")
    
    # Fetch odds from The Odds API
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        'apiKey': api_key,
        'regions': regions,
        'markets': markets,
        'oddsFormat': odds_format,
        'dateFormat': 'iso'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "sport": {
                    "key": sport_key,
                    "title": config.title,
                    "active": config.active
                },
                "games": data,
                "total_games": len(data),
                "markets": markets.split(','),
                "regions": regions.split(',')
            }
        else:
            error_data = response.json() if response.content else {"message": "Unknown error"}
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Odds API error: {error_data.get('message', 'Unknown error')}"
            )
            
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

@router.get("/")
async def get_all_active_odds(
    regions: str = Query(default="us", description="Comma-separated regions"),
    markets: str = Query(default="h2h", description="Comma-separated markets"),
    limit: int = Query(default=5, description="Max sports to fetch")
):
    """Get odds for all active sports (limited to prevent API overuse)"""
    
    active_sports = SportsConfigManager.get_active_sports()[:limit]
    api_key = os.getenv('ODDS_API_KEY')
    
    if not api_key:
        raise HTTPException(status_code=500, detail="Odds API key not configured")
    
    results = {}
    
    for config in active_sports:
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{config.key}/odds"
            params = {
                'apiKey': api_key,
                'regions': regions,
                'markets': markets,
                'oddsFormat': 'decimal',
                'dateFormat': 'iso'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results[config.key] = {
                    "sport_title": config.title,
                    "games": data,
                    "total_games": len(data)
                }
            else:
                results[config.key] = {
                    "sport_title": config.title,
                    "error": f"API error: {response.status_code}",
                    "games": [],
                    "total_games": 0
                }
                
        except Exception as e:
            results[config.key] = {
                "sport_title": config.title,
                "error": str(e),
                "games": [],
                "total_games": 0
            }
    
    return {
        "sports_data": results,
        "total_sports_fetched": len(results),
        "active_sports_available": len(SportsConfigManager.get_active_sports())
    }