"""
WNBA Arbitrage AI Tool - Odds API Endpoints
FastAPI endpoints for odds data and arbitrage detection
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional
import asyncio
from datetime import datetime

from app.services.odds_api import (
    get_wnba_odds, 
    find_arbitrage_opportunities, 
    get_provider_status,
    OddsAPIError
)

router = APIRouter(prefix="/api/v1/odds", tags=["odds"])


@router.get("/", response_model=Dict)
async def get_current_odds(
    bookmakers: Optional[str] = Query(None, description="Comma-separated list of bookmaker keys"),
    include_live: bool = Query(True, description="Include live/in-play odds"),
    background_tasks: BackgroundTasks = None
):
    """
    Get current WNBA odds from all available sources
    
    Args:
        bookmakers: Optional comma-separated list of specific bookmakers
        include_live: Whether to include live odds
        
    Returns:
        Aggregated odds data from all sources
    """
    try:
        # Parse bookmakers if provided
        bookmaker_list = None
        if bookmakers:
            bookmaker_list = [b.strip() for b in bookmakers.split(',')]
        
        # Get odds data
        odds_data = get_wnba_odds()
        
        # Filter by bookmakers if specified
        if bookmaker_list and 'sources' in odds_data:
            for source_name, source_data in odds_data['sources'].items():
                if 'data' in source_data and isinstance(source_data['data'], list):
                    for game in source_data['data']:
                        if 'bookmakers' in game:
                            game['bookmakers'] = [
                                book for book in game['bookmakers'] 
                                if book.get('key') in bookmaker_list
                            ]
        
        return odds_data
        
    except OddsAPIError as e:
        raise HTTPException(status_code=503, detail=f"Odds service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/arbitrage", response_model=List[Dict])
async def get_arbitrage_opportunities(
    min_profit: float = Query(0.01, ge=0.001, le=0.5, description="Minimum profit margin (0.01 = 1%)"),
    market_types: Optional[str] = Query(None, description="Comma-separated market types (h2h,spreads,totals)")
):
    """
    Find current arbitrage opportunities in WNBA betting markets
    
    Args:
        min_profit: Minimum profit margin to consider (1% = 0.01)
        market_types: Specific market types to analyze
        
    Returns:
        List of arbitrage opportunities found
    """
    try:
        opportunities = find_arbitrage_opportunities(min_profit)
        
        # Filter by market types if specified
        if market_types:
            allowed_markets = [m.strip() for m in market_types.split(',')]
            opportunities = [
                opp for opp in opportunities 
                if opp.get('market_type') in allowed_markets
            ]
        
        return opportunities
        
    except OddsAPIError as e:
        raise HTTPException(status_code=503, detail=f"Odds service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/arbitrage/summary", response_model=Dict)
async def get_arbitrage_summary(
    min_profit: float = Query(0.01, ge=0.001, le=0.5, description="Minimum profit margin")
):
    """
    Get summary statistics for current arbitrage opportunities
    
    Args:
        min_profit: Minimum profit margin to consider
        
    Returns:
        Summary statistics of arbitrage opportunities
    """
    try:
        opportunities = find_arbitrage_opportunities(min_profit)
        
        if not opportunities:
            return {
                "total_opportunities": 0,
                "average_profit": 0,
                "best_profit": 0,
                "markets_summary": {},
                "bookmakers_involved": [],
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
        
        # Calculate summary statistics
        profits = [opp['profit_percentage'] for opp in opportunities]
        market_counts = {}
        bookmakers = set()
        
        for opp in opportunities:
            market_type = opp.get('market_type', 'unknown')
            market_counts[market_type] = market_counts.get(market_type, 0) + 1
            
            # Extract bookmakers from best odds
            for outcome_data in opp.get('best_odds', {}).values():
                bookmakers.add(outcome_data.get('bookmaker'))
        
        summary = {
            "total_opportunities": len(opportunities),
            "average_profit": sum(profits) / len(profits),
            "best_profit": max(profits),
            "worst_profit": min(profits),
            "markets_summary": market_counts,
            "bookmakers_involved": sorted(list(bookmakers)),
            "profit_distribution": {
                "1-2%": len([p for p in profits if 1 <= p < 2]),
                "2-5%": len([p for p in profits if 2 <= p < 5]),
                "5%+": len([p for p in profits if p >= 5])
            },
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
        return summary
        
    except OddsAPIError as e:
        raise HTTPException(status_code=503, detail=f"Odds service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/providers/status", response_model=Dict)
async def get_providers_status():
    """
    Get status and health information for all odds providers
    
    Returns:
        Status information for each odds provider
    """
    try:
        status = get_provider_status()
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get provider status: {str(e)}")


@router.get("/games", response_model=List[Dict])
async def get_upcoming_games(
    days_ahead: int = Query(7, ge=1, le=30, description="Number of days ahead to look"),
    live_only: bool = Query(False, description="Only return live games")
):
    """
    Get upcoming WNBA games with basic information
    
    Args:
        days_ahead: Number of days ahead to look for games
        live_only: Only return currently live games
        
    Returns:
        List of upcoming WNBA games
    """
    try:
        odds_data = get_wnba_odds()
        games = []
        
        if 'sources' in odds_data and 'the_odds_api' in odds_data['sources']:
            api_data = odds_data['sources']['the_odds_api'].get('data', [])
            
            for game in api_data:
                game_info = {
                    "id": game.get('id'),
                    "sport_title": game.get('sport_title'),
                    "commence_time": game.get('commence_time'),
                    "home_team": game.get('home_team'),
                    "away_team": game.get('away_team'),
                    "bookmaker_count": len(game.get('bookmakers', [])),
                    "has_live_odds": any(
                        market.get('key') == 'h2h' 
                        for book in game.get('bookmakers', [])
                        for market in book.get('markets', [])
                    )
                }
                games.append(game_info)
        
        # Filter live games if requested
        if live_only:
            games = [g for g in games if g.get('has_live_odds')]
        
        # Sort by commence time
        games.sort(key=lambda x: x.get('commence_time', ''))
        
        return games
        
    except OddsAPIError as e:
        raise HTTPException(status_code=503, detail=f"Odds service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/bookmakers", response_model=List[str])
async def get_available_bookmakers():
    """
    Get list of available bookmakers from current odds data
    
    Returns:
        List of bookmaker keys currently providing odds
    """
    try:
        odds_data = get_wnba_odds()
        bookmakers = set()
        
        if 'sources' in odds_data and 'the_odds_api' in odds_data['sources']:
            api_data = odds_data['sources']['the_odds_api'].get('data', [])
            
            for game in api_data:
                for book in game.get('bookmakers', []):
                    bookmakers.add(book.get('key'))
        
        return sorted(list(bookmakers))
        
    except OddsAPIError as e:
        raise HTTPException(status_code=503, detail=f"Odds service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/health", response_model=Dict)
async def health_check():
    """
    Health check endpoint for the odds API
    
    Returns:
        Health status of the odds service
    """
    try:
        # Test basic functionality
        status = get_provider_status()
        
        health_info = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "providers_available": len(status.get('providers', {})),
            "providers_healthy": len([
                p for p in status.get('providers', {}).values() 
                if p.get('status') != 'error'
            ]),
            "service": "odds_api",
            "version": "1.0.0"
        }
        
        return health_info
        
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "service": "odds_api",
                "version": "1.0.0"
            }
        ) 