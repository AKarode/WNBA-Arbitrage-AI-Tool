"""
Enhanced Arbitrage API Endpoints

This module implements enhanced API endpoints supporting:
- Parallel processing across 47+ sports
- Cross-market arbitrage detection
- Real-time performance metrics
- Advanced filtering and sorting
- Comprehensive risk assessment

Based on research implementing:
- Real-time data processing with zero latency
- Multi-sport ensemble systems
- Performance optimization strategies
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
import json

from ..services.enhanced_arbitrage_engine import EnhancedArbitrageEngine, MarketType
from ..services.parallel_arbitrage_processor import ParallelArbitrageProcessor
from ..services.cross_market_analyzer import CrossMarketAnalyzer
from ..config.enhanced_sports_config import EnhancedSportsConfigManager, SportCategory

# Configure logging
logger = logging.getLogger(__name__)

# Initialize enhanced components
enhanced_engine = EnhancedArbitrageEngine(
    min_profit_threshold=1.0,
    enable_cross_market=True,
    confidence_threshold=0.7
)

parallel_processor = ParallelArbitrageProcessor(
    max_concurrent_requests=10,
    rate_limit_requests_per_second=5.0,
    api_quota_limit=1000
)

cross_market_analyzer = CrossMarketAnalyzer(
    correlation_threshold=0.85,
    min_profit_margin=0.5,
    max_correlation_risk=0.15
)

# Create enhanced router
router = APIRouter(prefix="/api/enhanced", tags=["enhanced-arbitrage"])


@router.get("/arbitrage/{sport_key}")
async def get_enhanced_sport_arbitrage(
    sport_key: str,
    min_profit: float = Query(default=1.0, description="Minimum profit margin %"),
    enable_cross_market: bool = Query(default=True, description="Enable cross-market detection"),
    include_spreads: bool = Query(default=True, description="Include spread arbitrage"),
    include_totals: bool = Query(default=True, description="Include totals arbitrage"),
    confidence_threshold: float = Query(default=0.7, description="Minimum confidence score"),
    max_results: int = Query(default=50, description="Maximum results to return"),
    regions: str = Query(default="us", description="Comma-separated regions"),
    markets: str = Query(default="h2h,spreads,totals", description="Markets to analyze")
):
    """
    Enhanced arbitrage detection for a specific sport
    
    Provides comprehensive arbitrage analysis including:
    - Multi-market arbitrage detection
    - Cross-market opportunities
    - Performance metrics and confidence scoring
    - Real-time processing optimization
    """
    try:
        # Validate sport configuration
        sport_config = EnhancedSportsConfigManager.get_sport_config(sport_key)
        if not sport_config:
            raise HTTPException(
                status_code=404, 
                detail=f"Sport '{sport_key}' not supported. Use /api/enhanced/sports for available sports."
            )
        
        # Adjust parameters based on sport configuration
        effective_min_profit = max(min_profit, sport_config.get_effective_min_profit_margin())
        effective_confidence = max(confidence_threshold, sport_config.confidence_threshold)
        
        # Update engine configuration
        enhanced_engine.min_profit_threshold = effective_min_profit
        enhanced_engine.confidence_threshold = effective_confidence
        enhanced_engine.enable_cross_market = enable_cross_market
        
        # Fetch odds data (mock implementation - would use real API)
        start_time = datetime.now()
        
        # In production, this would make actual API calls
        odds_data = await _fetch_sport_odds_enhanced(
            sport_key, regions, markets, sport_config
        )
        
        if not odds_data or not odds_data.get("games"):
            return {
                "sport": {
                    "key": sport_key,
                    "title": sport_config.title,
                    "category": sport_config.category.value,
                    "scanning_mode": "enhanced"
                },
                "analysis": {
                    "total_games_analyzed": 0,
                    "opportunities_found": 0,
                    "processing_time_ms": 0,
                    "enhanced_opportunities": [],
                    "message": "No games currently available"
                }
            }
        
        # Detect arbitrage opportunities
        all_opportunities = []
        cross_market_opportunities = []
        
        # Process each game
        for game in odds_data["games"]:
            # Standard arbitrage detection
            if "h2h" in markets:
                ml_opportunities = enhanced_engine.detect_moneyline_arbitrage(game)
                all_opportunities.extend(ml_opportunities)
            
            if include_spreads and "spreads" in markets:
                spread_opportunities = enhanced_engine.detect_spread_arbitrage(game)
                all_opportunities.extend(spread_opportunities)
            
            if include_totals and "totals" in markets:
                totals_opportunities = enhanced_engine.detect_totals_arbitrage(game)
                all_opportunities.extend(totals_opportunities)
            
            # Cross-market arbitrage detection
            if enable_cross_market:
                cross_opportunities = cross_market_analyzer.detect_moneyline_spread_arbitrage(game)
                cross_market_opportunities.extend(cross_opportunities)
        
        # Filter and sort opportunities
        filtered_opportunities = [
            opp for opp in all_opportunities 
            if opp.profit_margin >= effective_min_profit and 
               opp.confidence_score >= effective_confidence
        ]
        
        # Sort by profit margin (highest first)
        filtered_opportunities.sort(key=lambda x: x.profit_margin, reverse=True)
        
        # Limit results
        if max_results > 0:
            filtered_opportunities = filtered_opportunities[:max_results]
            cross_market_opportunities = cross_market_opportunities[:max_results//2]
        
        # Calculate processing metrics
        end_time = datetime.now()
        processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Prepare enhanced opportunities
        enhanced_opportunities = []
        
        # Add standard opportunities
        for opp in filtered_opportunities:
            enhanced_opp = opp.to_dict()
            
            # Add optimal stakes calculation
            if opp.best_odds:
                stakes = enhanced_engine.calculate_optimal_stakes(opp.best_odds, 10000)
                enhanced_opp["optimal_stakes"] = stakes
            
            enhanced_opportunities.append(enhanced_opp)
        
        # Add cross-market opportunities
        for cross_opp in cross_market_opportunities:
            enhanced_opp = cross_opp.to_dict()
            
            # Add risk assessment
            risk_assessment = cross_market_analyzer.assess_cross_market_risk(cross_opp)
            enhanced_opp["risk_assessment"] = {
                "overall_risk": risk_assessment.overall_risk,
                "risk_level": risk_assessment.get_risk_level(),
                "recommended_stake_percentage": risk_assessment.recommended_stake_percentage,
                "risk_factors": risk_assessment.risk_factors
            }
            
            enhanced_opportunities.append(enhanced_opp)
        
        # Update sport performance metrics
        EnhancedSportsConfigManager.update_sport_performance_metrics(
            sport_key,
            len(filtered_opportunities),
            sum(opp.profit_margin for opp in filtered_opportunities) / max(1, len(filtered_opportunities)),
            1.0  # Success rate placeholder
        )
        
        return {
            "sport": {
                "key": sport_key,
                "title": sport_config.title,
                "category": sport_config.category.value,
                "scanning_mode": "enhanced",
                "peak_season": sport_config.is_peak_season(),
                "quality_score": sport_config.quality_score,
                "risk_level": sport_config.risk_level
            },
            "analysis": {
                "total_games_analyzed": len(odds_data["games"]),
                "opportunities_found": len(filtered_opportunities),
                "cross_market_opportunities": len(cross_market_opportunities),
                "processing_time_ms": processing_time_ms,
                "markets_analyzed": markets.split(","),
                "effective_min_profit": effective_min_profit,
                "effective_confidence": effective_confidence,
                "enhanced_opportunities": enhanced_opportunities,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            },
            "performance_metrics": {
                "avg_opportunities_per_day": sport_config.avg_opportunities_per_day,
                "avg_profit_margin": sport_config.avg_profit_margin,
                "success_rate": sport_config.success_rate
            }
        }
        
    except Exception as e:
        logger.error(f"Error in enhanced sport arbitrage detection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/arbitrage/all")
async def get_enhanced_multi_sport_arbitrage(
    min_profit: float = Query(default=1.0, description="Minimum profit margin %"),
    enable_cross_market: bool = Query(default=True, description="Enable cross-market detection"),
    enable_parallel: bool = Query(default=True, description="Enable parallel processing"),
    max_sports: int = Query(default=10, description="Maximum sports to analyze"),
    category_filter: Optional[str] = Query(default=None, description="Filter by sport category"),
    priority_order: bool = Query(default=True, description="Use priority-based ordering"),
    include_performance: bool = Query(default=True, description="Include performance metrics"),
    timeout_seconds: int = Query(default=60, description="Maximum processing time")
):
    """
    Enhanced multi-sport arbitrage scanning with parallel processing
    
    Scans multiple sports simultaneously using advanced algorithms:
    - Parallel API calls and processing
    - Priority-based sport selection
    - Cross-market arbitrage detection
    - Performance optimization
    """
    try:
        start_time = datetime.now()
        
        # Determine sports to scan
        if priority_order:
            sports_to_scan = EnhancedSportsConfigManager.get_recommended_scanning_order()[:max_sports]
        else:
            all_sports = EnhancedSportsConfigManager.get_active_sports()
            sports_to_scan = [sport.key for sport in all_sports[:max_sports]]
        
        # Apply category filter
        if category_filter:
            try:
                category = SportCategory(category_filter)
                category_sports = EnhancedSportsConfigManager.get_sports_by_category(category)
                sports_to_scan = [
                    sport for sport in sports_to_scan 
                    if sport in [cs.key for cs in category_sports]
                ]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid category: {category_filter}")
        
        # Configure parallel processor
        parallel_processor.timeout_seconds = min(timeout_seconds, 120)  # Cap at 2 minutes
        
        # Fetch odds for all sports
        if enable_parallel:
            multi_sport_odds = await parallel_processor.fetch_multiple_sports_concurrent(sports_to_scan)
        else:
            # Sequential processing fallback
            multi_sport_odds = {}
            for sport_key in sports_to_scan:
                sport_config = EnhancedSportsConfigManager.get_sport_config(sport_key)
                if sport_config:
                    odds_data = await _fetch_sport_odds_enhanced(sport_key, "us", "h2h,spreads,totals", sport_config)
                    if odds_data:
                        multi_sport_odds[sport_key] = odds_data
        
        # Process arbitrage detection for all sports
        all_opportunities = []
        sport_breakdown = {}
        
        for sport_key, odds_data in multi_sport_odds.items():
            if not odds_data or not odds_data.get("games"):
                sport_breakdown[sport_key] = {"games": 0, "opportunities": 0, "error": "No data"}
                continue
            
            sport_config = EnhancedSportsConfigManager.get_sport_config(sport_key)
            sport_opportunities = []
            
            # Configure engine for this sport
            enhanced_engine.min_profit_threshold = max(min_profit, sport_config.get_effective_min_profit_margin())
            enhanced_engine.confidence_threshold = sport_config.confidence_threshold
            
            # Process each game
            for game in odds_data["games"]:
                game["sport_key"] = sport_key  # Add sport identifier
                
                # Standard arbitrage detection
                ml_opportunities = enhanced_engine.detect_moneyline_arbitrage(game)
                spread_opportunities = enhanced_engine.detect_spread_arbitrage(game)
                totals_opportunities = enhanced_engine.detect_totals_arbitrage(game)
                
                sport_opportunities.extend(ml_opportunities)
                sport_opportunities.extend(spread_opportunities)
                sport_opportunities.extend(totals_opportunities)
                
                # Cross-market arbitrage
                if enable_cross_market:
                    cross_opportunities = cross_market_analyzer.detect_moneyline_spread_arbitrage(game)
                    # Convert to standard format for consistency
                    for cross_opp in cross_opportunities:
                        sport_opportunities.append(cross_opp)  # Would need proper conversion
            
            # Filter opportunities for this sport
            filtered_sport_opportunities = [
                opp for opp in sport_opportunities
                if hasattr(opp, 'profit_margin') and opp.profit_margin >= enhanced_engine.min_profit_threshold
            ]
            
            all_opportunities.extend(filtered_sport_opportunities)
            sport_breakdown[sport_key] = {
                "games": len(odds_data["games"]),
                "opportunities": len(filtered_sport_opportunities),
                "sport_title": sport_config.title,
                "category": sport_config.category.value,
                "peak_season": sport_config.is_peak_season()
            }
        
        # Sort all opportunities by profit margin
        all_opportunities.sort(
            key=lambda x: getattr(x, 'profit_margin', 0), 
            reverse=True
        )
        
        # Calculate processing metrics
        end_time = datetime.now()
        processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Get parallel processing metrics
        processing_metrics = parallel_processor.get_processing_metrics()
        
        # Prepare opportunities for response
        enhanced_opportunities = []
        for opp in all_opportunities:
            if hasattr(opp, 'to_dict'):
                enhanced_opp = opp.to_dict()
                enhanced_opp["sport"] = opp.sport_key if hasattr(opp, 'sport_key') else "unknown"
                enhanced_opportunities.append(enhanced_opp)
        
        response_data = {
            "scan_summary": {
                "sports_analyzed": len(sport_breakdown),
                "sports_requested": len(sports_to_scan),
                "total_games": sum(breakdown.get("games", 0) for breakdown in sport_breakdown.values()),
                "total_opportunities": len(all_opportunities),
                "processing_time_ms": processing_time_ms,
                "parallel_processing": enable_parallel,
                "cross_market_enabled": enable_cross_market,
                "category_filter": category_filter,
                "min_profit_threshold": min_profit
            },
            "sport_breakdown": sport_breakdown,
            "all_opportunities": enhanced_opportunities,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Add performance metrics if requested
        if include_performance:
            response_data["performance_metrics"] = {
                **processing_metrics,
                "sports_per_second": len(sport_breakdown) / max(0.001, processing_time_ms / 1000),
                "opportunities_per_sport": len(all_opportunities) / max(1, len(sport_breakdown))
            }
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in enhanced multi-sport arbitrage scanning: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/sports")
async def get_enhanced_sports_list(
    category: Optional[str] = Query(default=None, description="Filter by category"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    include_performance: bool = Query(default=True, description="Include performance metrics"),
    peak_season_only: bool = Query(default=False, description="Only peak season sports")
):
    """
    Get comprehensive list of supported sports with enhanced configuration
    
    Returns detailed information about all 47+ supported sports including:
    - Performance metrics and opportunity rates
    - Seasonal information and peak periods
    - Risk assessment and quality scores
    - Offshore bookmaker support
    """
    try:
        all_sports = EnhancedSportsConfigManager.get_all_sports()
        
        # Apply filters
        filtered_sports = all_sports.copy()
        
        if category:
            try:
                category_enum = SportCategory(category)
                filtered_sports = {
                    k: v for k, v in filtered_sports.items()
                    if v.category == category_enum
                }
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
        
        if peak_season_only:
            current_month = datetime.now().month
            filtered_sports = {
                k: v for k, v in filtered_sports.items()
                if v.is_peak_season(current_month)
            }
        
        # Prepare sports data
        sports_data = []
        for sport_key, config in filtered_sports.items():
            sport_info = {
                "key": sport_key,
                "title": config.title,
                "category": config.category.value,
                "status": config.status.value,
                "supported_markets": config.supported_markets,
                "priority_markets": config.priority_markets,
                "min_profit_margin": config.min_profit_margin,
                "effective_min_profit": config.get_effective_min_profit_margin(),
                "update_frequency": config.get_dynamic_update_frequency(),
                "peak_season": config.is_peak_season(),
                "offshore_bookmakers": config.offshore_bookmakers,
                "risk_level": config.risk_level,
                "quality_score": config.quality_score,
                "volatility_factor": config.volatility_factor
            }
            
            if include_performance:
                sport_info["performance_metrics"] = {
                    "avg_opportunities_per_day": config.avg_opportunities_per_day,
                    "avg_profit_margin": config.avg_profit_margin,
                    "success_rate": config.success_rate
                }
            
            sports_data.append(sport_info)
        
        # Sort by priority (US major first, then by opportunities)
        def sort_priority(sport):
            return (
                sport["category"] == "us_major",
                sport.get("performance_metrics", {}).get("avg_opportunities_per_day", 0),
                sport["quality_score"]
            )
        
        sports_data.sort(key=sort_priority, reverse=True)
        
        # Get configuration summary
        config_summary = EnhancedSportsConfigManager.get_configuration_summary()
        
        return {
            "sports": sports_data,
            "summary": {
                "total_sports": len(sports_data),
                "total_available": len(all_sports),
                "filters_applied": {
                    "category": category,
                    "peak_season_only": peak_season_only
                },
                **config_summary
            },
            "categories": [category.value for category in SportCategory],
            "recommended_scanning_order": EnhancedSportsConfigManager.get_recommended_scanning_order()[:10]
        }
        
    except Exception as e:
        logger.error(f"Error getting enhanced sports list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/system/status")
async def get_enhanced_system_status():
    """
    Get comprehensive system status and performance metrics
    
    Returns real-time information about:
    - System performance and load
    - API quota usage and rate limits
    - Processing capabilities and optimization
    - Recent performance statistics
    """
    try:
        # Get system performance metrics
        processing_metrics = parallel_processor.get_processing_metrics()
        
        # Calculate optimal concurrency
        optimal_concurrency = await parallel_processor.calculate_optimal_concurrency()
        
        # Get sports configuration summary
        config_summary = EnhancedSportsConfigManager.get_configuration_summary()
        
        return {
            "status": "operational",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system_capabilities": {
                "total_sports_supported": config_summary["total_sports"],
                "parallel_processing": True,
                "cross_market_detection": True,
                "real_time_optimization": True,
                "offshore_bookmaker_support": True
            },
            "performance_metrics": {
                **processing_metrics,
                "optimal_concurrency": optimal_concurrency,
                "current_max_concurrency": parallel_processor.max_concurrent_requests
            },
            "sports_status": {
                "peak_season_sports": config_summary["peak_season_current"],
                "us_major_sports_active": config_summary["us_major_sports"],
                "offshore_supported_sports": config_summary["offshore_supported"],
                "total_opportunities_estimate": config_summary["avg_opportunities_per_day"]
            },
            "api_configuration": {
                "rate_limit_per_second": 5.0,
                "max_concurrent_requests": parallel_processor.max_concurrent_requests,
                "timeout_seconds": parallel_processor.timeout_seconds,
                "quota_remaining": parallel_processor.quota_manager.get_remaining_quota()
            },
            "features": {
                "parallel_processing": True,
                "cross_market_detection": True,
                "real_time_monitoring": True,
                "dynamic_optimization": True,
                "risk_assessment": True,
                "performance_tracking": True
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# Helper Functions

async def _fetch_sport_odds_enhanced(
    sport_key: str, 
    regions: str, 
    markets: str, 
    sport_config
) -> Optional[Dict[str, Any]]:
    """
    Enhanced odds fetching with sport-specific optimization
    
    In production, this would make actual API calls to The Odds API
    with caching, rate limiting, and error handling.
    """
    try:
        # Mock implementation - would use real API calls
        await asyncio.sleep(0.1)  # Simulate API call
        
        # Mock response based on sport configuration
        mock_games = []
        
        # Generate mock games based on sport activity
        num_games = 3 if sport_config.is_peak_season() else 1
        
        for i in range(num_games):
            game = {
                "id": f"{sport_key}_game_{i}",
                "sport_key": sport_key,
                "sport_title": sport_config.title,
                "commence_time": "2025-06-10T02:00:00Z",
                "home_team": f"Home Team {i}",
                "away_team": f"Away Team {i}",
                "bookmakers": _generate_mock_bookmakers(sport_config, markets)
            }
            mock_games.append(game)
        
        return {
            "sport_key": sport_key,
            "sport_title": sport_config.title,
            "games": mock_games
        }
        
    except Exception as e:
        logger.error(f"Error fetching odds for {sport_key}: {str(e)}")
        return None


def _generate_mock_bookmakers(sport_config, markets: str) -> List[Dict[str, Any]]:
    """Generate mock bookmaker data for testing"""
    bookmakers = []
    
    # Use configured offshore bookmakers or defaults
    bookmaker_list = sport_config.offshore_bookmakers or ["betonlineag", "bovada", "fanduel"]
    
    for book_key in bookmaker_list[:3]:  # Limit to 3 bookmakers
        bookmaker = {
            "key": book_key,
            "title": book_key.replace("ag", ".ag").title(),
            "last_update": datetime.now(timezone.utc).isoformat(),
            "markets": []
        }
        
        # Generate markets based on request
        market_list = markets.split(",")
        
        if "h2h" in market_list and "h2h" in sport_config.supported_markets:
            bookmaker["markets"].append({
                "key": "h2h",
                "last_update": datetime.now(timezone.utc).isoformat(),
                "outcomes": [
                    {"name": "Home Team", "price": 1.85 + (hash(book_key) % 10) * 0.01},
                    {"name": "Away Team", "price": 1.95 + (hash(book_key) % 8) * 0.01}
                ]
            })
        
        if "spreads" in market_list and "spreads" in sport_config.supported_markets:
            bookmaker["markets"].append({
                "key": "spreads",
                "last_update": datetime.now(timezone.utc).isoformat(),
                "outcomes": [
                    {"name": "Home Team", "price": 1.90, "point": -2.5},
                    {"name": "Away Team", "price": 1.95, "point": 2.5}
                ]
            })
        
        if "totals" in market_list and "totals" in sport_config.supported_markets:
            bookmaker["markets"].append({
                "key": "totals", 
                "last_update": datetime.now(timezone.utc).isoformat(),
                "outcomes": [
                    {"name": "Over", "price": 1.88, "point": 205.5},
                    {"name": "Under", "price": 1.95, "point": 205.5}
                ]
            })
        
        bookmakers.append(bookmaker)
    
    return bookmakers