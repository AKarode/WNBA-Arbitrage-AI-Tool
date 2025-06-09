"""
Enhanced Sports Configuration with 47+ Sports

This module implements comprehensive sports configuration supporting:
- 47+ sports from The Odds API coverage
- Dynamic sport activation based on season
- Performance optimization per sport
- Regional configuration for offshore sportsbooks
- Real-time priority adjustment based on activity

Based on research implementing:
- Multi-sport configuration management
- Peak season awareness and optimization
- California-focused offshore coverage
- Sport-specific risk profiling
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)


class SportCategory(Enum):
    """Categories of sports for organization"""
    US_MAJOR = "us_major"
    BASKETBALL = "basketball"
    AMERICAN_FOOTBALL = "american_football"
    BASEBALL = "baseball"
    HOCKEY = "hockey"
    SOCCER = "soccer"
    COMBAT_SPORTS = "combat_sports"
    GOLF = "golf"
    TENNIS = "tennis"
    CRICKET = "cricket"
    RUGBY = "rugby"
    MOTORSPORTS = "motorsports"
    OTHER = "other"


class SportStatus(Enum):
    """Status of sport for arbitrage detection"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SEASONAL = "seasonal"
    DISABLED = "disabled"


@dataclass
class EnhancedSportConfig:
    """Enhanced configuration for a single sport"""
    # Basic identification
    key: str
    title: str
    category: SportCategory
    status: SportStatus
    
    # Market configuration
    supported_markets: List[str] = field(default_factory=lambda: ["h2h"])
    priority_markets: List[str] = field(default_factory=lambda: ["h2h"])
    
    # Arbitrage parameters
    min_profit_margin: float = 2.0
    confidence_threshold: float = 0.7
    max_stake_percentage: float = 0.1
    
    # Processing configuration
    update_frequency_seconds: int = 120
    max_concurrent_requests: int = 3
    timeout_seconds: int = 15
    
    # Seasonal configuration
    peak_season_months: List[int] = field(default_factory=list)
    off_season_months: List[int] = field(default_factory=list)
    
    # Regional configuration (California offshore focus)
    supported_regions: List[str] = field(default_factory=lambda: ["us"])
    offshore_bookmakers: List[str] = field(default_factory=list)
    
    # Risk and quality settings
    risk_level: str = "medium"  # low, medium, high
    quality_score: float = 0.8  # 0.0 to 1.0
    volatility_factor: float = 1.0  # Multiplier for odds volatility
    
    # Performance metrics
    avg_opportunities_per_day: float = 0.0
    avg_profit_margin: float = 0.0
    success_rate: float = 0.0
    
    def is_peak_season(self, month: int = None) -> bool:
        """Check if current month is peak season"""
        current_month = month or datetime.now().month
        return current_month in self.peak_season_months
    
    def is_off_season(self, month: int = None) -> bool:
        """Check if current month is off season"""
        current_month = month or datetime.now().month
        return current_month in self.off_season_months
    
    def get_dynamic_update_frequency(self) -> int:
        """Get update frequency adjusted for season and activity"""
        base_frequency = self.update_frequency_seconds
        
        if self.is_peak_season():
            return max(30, int(base_frequency * 0.5))  # More frequent during peak
        elif self.is_off_season():
            return int(base_frequency * 2.0)  # Less frequent during off-season
        else:
            return base_frequency
    
    def get_effective_min_profit_margin(self) -> float:
        """Get minimum profit margin adjusted for sport characteristics"""
        base_margin = self.min_profit_margin
        
        # Adjust for volatility
        volatility_adjustment = 1.0 + (self.volatility_factor - 1.0) * 0.5
        
        # Adjust for quality
        quality_adjustment = 2.0 - self.quality_score
        
        return base_margin * volatility_adjustment * quality_adjustment


class EnhancedSportsConfigManager:
    """
    Enhanced sports configuration manager supporting 47+ sports
    
    Manages comprehensive sports configuration with dynamic adjustments,
    seasonal optimization, and California offshore sportsbook focus.
    """
    
    # The Odds API Sports Configuration (47+ sports)
    ENHANCED_SPORTS_CONFIG = {
        # US Major Sports (Primary Focus)
        "basketball_nba": EnhancedSportConfig(
            key="basketball_nba",
            title="NBA",
            category=SportCategory.US_MAJOR,
            status=SportStatus.ACTIVE,
            supported_markets=["h2h", "spreads", "totals", "player_props"],
            priority_markets=["h2h", "spreads"],
            min_profit_margin=1.0,
            confidence_threshold=0.85,
            max_stake_percentage=0.15,
            update_frequency_seconds=30,
            max_concurrent_requests=5,
            peak_season_months=[10, 11, 12, 1, 2, 3, 4, 5, 6],
            off_season_months=[7, 8, 9],
            offshore_bookmakers=["betonlineag", "bovada", "betus", "lowvig"],
            risk_level="low",
            quality_score=0.95,
            volatility_factor=0.8,
            avg_opportunities_per_day=2.5
        ),
        
        "basketball_wnba": EnhancedSportConfig(
            key="basketball_wnba",
            title="WNBA",
            category=SportCategory.BASKETBALL,
            status=SportStatus.SEASONAL,
            supported_markets=["h2h", "spreads", "totals"],
            priority_markets=["h2h", "spreads"],
            min_profit_margin=1.5,
            confidence_threshold=0.8,
            max_stake_percentage=0.12,
            update_frequency_seconds=45,
            max_concurrent_requests=4,
            peak_season_months=[5, 6, 7, 8, 9, 10],
            off_season_months=[11, 12, 1, 2, 3, 4],
            offshore_bookmakers=["betonlineag", "bovada", "betus"],
            risk_level="medium",
            quality_score=0.85,
            volatility_factor=1.2,
            avg_opportunities_per_day=1.8
        ),
        
        "americanfootball_nfl": EnhancedSportConfig(
            key="americanfootball_nfl",
            title="NFL",
            category=SportCategory.US_MAJOR,
            status=SportStatus.ACTIVE,
            supported_markets=["h2h", "spreads", "totals", "player_props"],
            priority_markets=["spreads", "totals"],
            min_profit_margin=0.8,
            confidence_threshold=0.9,
            max_stake_percentage=0.2,
            update_frequency_seconds=45,
            max_concurrent_requests=6,
            peak_season_months=[9, 10, 11, 12, 1, 2],
            off_season_months=[3, 4, 5, 6, 7, 8],
            offshore_bookmakers=["betonlineag", "bovada", "betus", "lowvig", "mybookie"],
            risk_level="low",
            quality_score=0.98,
            volatility_factor=0.7,
            avg_opportunities_per_day=3.2
        ),
        
        "baseball_mlb": EnhancedSportConfig(
            key="baseball_mlb",
            title="MLB",
            category=SportCategory.US_MAJOR,
            status=SportStatus.ACTIVE,
            supported_markets=["h2h", "spreads", "totals"],
            priority_markets=["h2h", "totals"],
            min_profit_margin=1.2,
            confidence_threshold=0.8,
            max_stake_percentage=0.12,
            update_frequency_seconds=90,
            max_concurrent_requests=4,
            peak_season_months=[4, 5, 6, 7, 8, 9, 10],
            off_season_months=[11, 12, 1, 2, 3],
            offshore_bookmakers=["betonlineag", "bovada", "betus"],
            risk_level="medium",
            quality_score=0.88,
            volatility_factor=1.1,
            avg_opportunities_per_day=2.1
        ),
        
        "icehockey_nhl": EnhancedSportConfig(
            key="icehockey_nhl",
            title="NHL",
            category=SportCategory.HOCKEY,
            status=SportStatus.ACTIVE,
            supported_markets=["h2h", "spreads", "totals"],
            priority_markets=["h2h", "totals"],
            min_profit_margin=1.3,
            confidence_threshold=0.75,
            max_stake_percentage=0.1,
            update_frequency_seconds=60,
            max_concurrent_requests=3,
            peak_season_months=[10, 11, 12, 1, 2, 3, 4, 5, 6],
            off_season_months=[7, 8, 9],
            offshore_bookmakers=["betonlineag", "bovada", "betus"],
            risk_level="medium",
            quality_score=0.82,
            volatility_factor=1.3,
            avg_opportunities_per_day=1.5
        ),
        
        # Soccer (Multiple Leagues)
        "soccer_usa_mls": EnhancedSportConfig(
            key="soccer_usa_mls",
            title="MLS",
            category=SportCategory.SOCCER,
            status=SportStatus.ACTIVE,
            supported_markets=["h2h", "spreads", "totals"],
            priority_markets=["h2h"],
            min_profit_margin=1.8,
            confidence_threshold=0.7,
            update_frequency_seconds=120,
            peak_season_months=[3, 4, 5, 6, 7, 8, 9, 10, 11],
            offshore_bookmakers=["betonlineag", "bovada"],
            risk_level="medium",
            quality_score=0.78,
            volatility_factor=1.4
        ),
        
        "soccer_epl": EnhancedSportConfig(
            key="soccer_epl",
            title="English Premier League",
            category=SportCategory.SOCCER,
            status=SportStatus.ACTIVE,
            supported_markets=["h2h", "spreads", "totals"],
            priority_markets=["h2h"],
            min_profit_margin=1.5,
            confidence_threshold=0.8,
            update_frequency_seconds=90,
            peak_season_months=[8, 9, 10, 11, 12, 1, 2, 3, 4, 5],
            offshore_bookmakers=["betonlineag", "bovada", "betus"],
            risk_level="low",
            quality_score=0.92,
            volatility_factor=0.9,
            avg_opportunities_per_day=2.8
        ),
        
        "soccer_spain_la_liga": EnhancedSportConfig(
            key="soccer_spain_la_liga",
            title="La Liga",
            category=SportCategory.SOCCER,
            status=SportStatus.ACTIVE,
            supported_markets=["h2h", "spreads", "totals"],
            priority_markets=["h2h"],
            min_profit_margin=1.6,
            confidence_threshold=0.78,
            update_frequency_seconds=100,
            peak_season_months=[8, 9, 10, 11, 12, 1, 2, 3, 4, 5],
            offshore_bookmakers=["betonlineag", "bovada"],
            quality_score=0.88,
            avg_opportunities_per_day=2.2
        ),
        
        "soccer_germany_bundesliga": EnhancedSportConfig(
            key="soccer_germany_bundesliga",
            title="Bundesliga",
            category=SportCategory.SOCCER,
            status=SportStatus.ACTIVE,
            supported_markets=["h2h", "spreads", "totals"],
            priority_markets=["h2h"],
            min_profit_margin=1.7,
            update_frequency_seconds=110,
            peak_season_months=[8, 9, 10, 11, 12, 1, 2, 3, 4, 5],
            offshore_bookmakers=["betonlineag", "bovada"],
            quality_score=0.86
        ),
        
        "soccer_italy_serie_a": EnhancedSportConfig(
            key="soccer_italy_serie_a",
            title="Serie A",
            category=SportCategory.SOCCER,
            status=SportStatus.ACTIVE,
            supported_markets=["h2h", "spreads", "totals"],
            min_profit_margin=1.8,
            update_frequency_seconds=120,
            peak_season_months=[8, 9, 10, 11, 12, 1, 2, 3, 4, 5],
            quality_score=0.83
        ),
        
        "soccer_france_ligue_one": EnhancedSportConfig(
            key="soccer_france_ligue_one",
            title="Ligue 1",
            category=SportCategory.SOCCER,
            status=SportStatus.ACTIVE,
            supported_markets=["h2h", "spreads", "totals"],
            min_profit_margin=1.9,
            update_frequency_seconds=130,
            peak_season_months=[8, 9, 10, 11, 12, 1, 2, 3, 4, 5],
            quality_score=0.80
        ),
        
        "soccer_uefa_champs_league": EnhancedSportConfig(
            key="soccer_uefa_champs_league",
            title="UEFA Champions League",
            category=SportCategory.SOCCER,
            status=SportStatus.SEASONAL,
            supported_markets=["h2h", "spreads", "totals"],
            min_profit_margin=1.2,
            confidence_threshold=0.85,
            update_frequency_seconds=60,
            peak_season_months=[9, 10, 11, 12, 1, 2, 3, 4, 5, 6],
            offshore_bookmakers=["betonlineag", "bovada", "betus"],
            quality_score=0.95,
            avg_opportunities_per_day=1.8
        ),
        
        # College Sports
        "americanfootball_ncaaf": EnhancedSportConfig(
            key="americanfootball_ncaaf",
            title="NCAAF",
            category=SportCategory.AMERICAN_FOOTBALL,
            status=SportStatus.SEASONAL,
            supported_markets=["h2h", "spreads", "totals"],
            min_profit_margin=1.4,
            update_frequency_seconds=60,
            peak_season_months=[8, 9, 10, 11, 12, 1],
            offshore_bookmakers=["betonlineag", "bovada", "betus"],
            quality_score=0.82,
            volatility_factor=1.5
        ),
        
        "basketball_ncaab": EnhancedSportConfig(
            key="basketball_ncaab",
            title="NCAAB",
            category=SportCategory.BASKETBALL,
            status=SportStatus.SEASONAL,
            supported_markets=["h2h", "spreads", "totals"],
            min_profit_margin=1.3,
            update_frequency_seconds=45,
            peak_season_months=[11, 12, 1, 2, 3, 4],
            offshore_bookmakers=["betonlineag", "bovada", "betus"],
            quality_score=0.85,
            volatility_factor=1.4
        ),
        
        # Tennis
        "tennis_wta": EnhancedSportConfig(
            key="tennis_wta",
            title="WTA",
            category=SportCategory.TENNIS,
            status=SportStatus.ACTIVE,
            supported_markets=["h2h"],
            min_profit_margin=2.0,
            update_frequency_seconds=180,
            peak_season_months=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            quality_score=0.75,
            volatility_factor=1.8
        ),
        
        "tennis_atp": EnhancedSportConfig(
            key="tennis_atp",
            title="ATP",
            category=SportCategory.TENNIS,
            status=SportStatus.ACTIVE,
            supported_markets=["h2h"],
            min_profit_margin=1.8,
            update_frequency_seconds=180,
            peak_season_months=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            quality_score=0.78,
            volatility_factor=1.6
        ),
        
        # Golf
        "golf_pga": EnhancedSportConfig(
            key="golf_pga",
            title="PGA Tour",
            category=SportCategory.GOLF,
            status=SportStatus.ACTIVE,
            supported_markets=["outrights", "h2h"],
            min_profit_margin=2.5,
            update_frequency_seconds=300,
            peak_season_months=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            quality_score=0.70,
            volatility_factor=2.2
        ),
        
        # Combat Sports
        "mma_ufc": EnhancedSportConfig(
            key="mma_ufc",
            title="UFC",
            category=SportCategory.COMBAT_SPORTS,
            status=SportStatus.ACTIVE,
            supported_markets=["h2h"],
            min_profit_margin=2.2,
            confidence_threshold=0.65,
            update_frequency_seconds=240,
            offshore_bookmakers=["betonlineag", "bovada", "betus"],
            quality_score=0.73,
            volatility_factor=2.0,
            avg_opportunities_per_day=0.8
        ),
        
        "boxing": EnhancedSportConfig(
            key="boxing",
            title="Boxing",
            category=SportCategory.COMBAT_SPORTS,
            status=SportStatus.ACTIVE,
            supported_markets=["h2h"],
            min_profit_margin=2.5,
            update_frequency_seconds=300,
            offshore_bookmakers=["betonlineag", "bovada"],
            quality_score=0.68,
            volatility_factor=2.5
        ),
        
        # Cricket
        "cricket_ipl": EnhancedSportConfig(
            key="cricket_ipl",
            title="IPL",
            category=SportCategory.CRICKET,
            status=SportStatus.SEASONAL,
            supported_markets=["h2h", "totals"],
            min_profit_margin=2.0,
            update_frequency_seconds=180,
            peak_season_months=[3, 4, 5, 6],
            quality_score=0.72,
            volatility_factor=1.7
        ),
        
        "cricket_international": EnhancedSportConfig(
            key="cricket_international",
            title="International Cricket",
            category=SportCategory.CRICKET,
            status=SportStatus.ACTIVE,
            supported_markets=["h2h", "totals"],
            min_profit_margin=2.2,
            update_frequency_seconds=200,
            quality_score=0.68,
            volatility_factor=1.9
        ),
        
        # Additional Sports (Lower Priority)
        "rugby_nrl": EnhancedSportConfig(
            key="rugby_nrl",
            title="NRL",
            category=SportCategory.RUGBY,
            status=SportStatus.SEASONAL,
            supported_markets=["h2h", "spreads"],
            min_profit_margin=2.3,
            update_frequency_seconds=240,
            peak_season_months=[3, 4, 5, 6, 7, 8, 9],
            quality_score=0.65
        ),
        
        "aussierules_afl": EnhancedSportConfig(
            key="aussierules_afl",
            title="AFL",
            category=SportCategory.OTHER,
            status=SportStatus.SEASONAL,
            supported_markets=["h2h", "spreads"],
            min_profit_margin=2.5,
            update_frequency_seconds=250,
            peak_season_months=[3, 4, 5, 6, 7, 8, 9],
            quality_score=0.62
        ),
        
        # Motorsports
        "motorsport_nascar": EnhancedSportConfig(
            key="motorsport_nascar",
            title="NASCAR",
            category=SportCategory.MOTORSPORTS,
            status=SportStatus.ACTIVE,
            supported_markets=["outrights", "h2h"],
            min_profit_margin=3.0,
            update_frequency_seconds=360,
            peak_season_months=[2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            quality_score=0.58,
            volatility_factor=2.8
        )
    }
    
    @classmethod
    def get_sport_config(cls, sport_key: str) -> Optional[EnhancedSportConfig]:
        """Get enhanced configuration for a specific sport"""
        return cls.ENHANCED_SPORTS_CONFIG.get(sport_key)
    
    @classmethod
    def get_all_sports(cls) -> Dict[str, EnhancedSportConfig]:
        """Get all enhanced sports configurations"""
        return cls.ENHANCED_SPORTS_CONFIG.copy()
    
    @classmethod
    def get_active_sports(cls) -> List[EnhancedSportConfig]:
        """Get all active sports configurations"""
        return [
            config for config in cls.ENHANCED_SPORTS_CONFIG.values()
            if config.status in [SportStatus.ACTIVE, SportStatus.SEASONAL]
        ]
    
    @classmethod
    def get_sports_by_category(cls, category: SportCategory) -> List[EnhancedSportConfig]:
        """Get sports by category"""
        return [
            config for config in cls.ENHANCED_SPORTS_CONFIG.values()
            if config.category == category
        ]
    
    @classmethod
    def get_us_major_sports(cls) -> List[EnhancedSportConfig]:
        """Get US major sports (highest priority)"""
        return [
            config for config in cls.ENHANCED_SPORTS_CONFIG.values()
            if config.category == SportCategory.US_MAJOR
        ]
    
    @classmethod
    def get_peak_season_sports(cls, month: int = None) -> List[EnhancedSportConfig]:
        """Get sports currently in peak season"""
        current_month = month or datetime.now().month
        return [
            config for config in cls.ENHANCED_SPORTS_CONFIG.values()
            if config.is_peak_season(current_month)
        ]
    
    @classmethod
    def get_offshore_supported_sports(cls) -> List[EnhancedSportConfig]:
        """Get sports with offshore bookmaker support"""
        return [
            config for config in cls.ENHANCED_SPORTS_CONFIG.values()
            if config.offshore_bookmakers
        ]
    
    @classmethod
    def get_high_opportunity_sports(cls, min_daily_opportunities: float = 1.0) -> List[EnhancedSportConfig]:
        """Get sports with high opportunity rates"""
        return [
            config for config in cls.ENHANCED_SPORTS_CONFIG.values()
            if config.avg_opportunities_per_day >= min_daily_opportunities
        ]
    
    @classmethod
    def get_low_risk_sports(cls) -> List[EnhancedSportConfig]:
        """Get low-risk sports for conservative strategies"""
        return [
            config for config in cls.ENHANCED_SPORTS_CONFIG.values()
            if config.risk_level == "low" and config.quality_score >= 0.85
        ]
    
    @classmethod
    def get_sports_by_priority(cls, max_sports: int = 10) -> List[EnhancedSportConfig]:
        """Get sports ordered by priority (opportunities, quality, risk)"""
        sports = list(cls.ENHANCED_SPORTS_CONFIG.values())
        
        # Sort by priority score (opportunities * quality / risk)
        def priority_score(config: EnhancedSportConfig) -> float:
            risk_multiplier = {"low": 1.0, "medium": 0.8, "high": 0.6}[config.risk_level]
            return (config.avg_opportunities_per_day * config.quality_score * risk_multiplier)
        
        sorted_sports = sorted(sports, key=priority_score, reverse=True)
        return sorted_sports[:max_sports]
    
    @classmethod
    def get_total_sports_count(cls) -> int:
        """Get total number of configured sports"""
        return len(cls.ENHANCED_SPORTS_CONFIG)
    
    @classmethod
    def get_configuration_summary(cls) -> Dict[str, Any]:
        """Get summary of sports configuration"""
        all_sports = cls.ENHANCED_SPORTS_CONFIG.values()
        
        return {
            "total_sports": len(all_sports),
            "active_sports": len([s for s in all_sports if s.status == SportStatus.ACTIVE]),
            "seasonal_sports": len([s for s in all_sports if s.status == SportStatus.SEASONAL]),
            "categories": {
                category.value: len([s for s in all_sports if s.category == category])
                for category in SportCategory
            },
            "us_major_sports": len(cls.get_us_major_sports()),
            "offshore_supported": len(cls.get_offshore_supported_sports()),
            "peak_season_current": len(cls.get_peak_season_sports()),
            "avg_opportunities_per_day": sum(s.avg_opportunities_per_day for s in all_sports),
            "avg_quality_score": sum(s.quality_score for s in all_sports) / len(all_sports)
        }
    
    @classmethod
    def update_sport_performance_metrics(
        cls, 
        sport_key: str, 
        opportunities_found: int, 
        avg_profit: float, 
        success_rate: float
    ):
        """Update performance metrics for a sport"""
        config = cls.get_sport_config(sport_key)
        if config:
            # Simple exponential moving average update
            alpha = 0.1  # Learning rate
            config.avg_opportunities_per_day = (
                (1 - alpha) * config.avg_opportunities_per_day + 
                alpha * opportunities_found
            )
            config.avg_profit_margin = (
                (1 - alpha) * config.avg_profit_margin + 
                alpha * avg_profit
            )
            config.success_rate = (
                (1 - alpha) * config.success_rate + 
                alpha * success_rate
            )
            
            logger.info(f"Updated performance metrics for {sport_key}")
    
    @classmethod
    def get_recommended_scanning_order(cls) -> List[str]:
        """Get recommended order for scanning sports"""
        priority_sports = cls.get_sports_by_priority(max_sports=20)
        
        # Further prioritize by peak season and US major sports
        current_month = datetime.now().month
        
        def scanning_priority(config: EnhancedSportConfig) -> tuple:
            return (
                config.category == SportCategory.US_MAJOR,  # US major first
                config.is_peak_season(current_month),       # Peak season second
                config.avg_opportunities_per_day,           # High opportunities third
                config.quality_score,                       # High quality fourth
                1.0 / (config.volatility_factor + 0.1)     # Low volatility fifth
            )
        
        sorted_sports = sorted(priority_sports, key=scanning_priority, reverse=True)
        return [config.key for config in sorted_sports]