"""
Multi-sport configuration for arbitrage detection
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class SportConfig:
    key: str
    title: str
    active: bool
    markets: List[str]
    update_frequency: int  # seconds
    min_profit_margin: float  # percentage
    peak_season_months: List[int]
    
class SportsConfigManager:
    """Centralized configuration for all supported sports"""
    
    SPORTS_CONFIG = {
        "basketball_nba": SportConfig(
            key="basketball_nba",
            title="NBA",
            active=True,
            markets=["h2h", "spreads", "totals"],
            update_frequency=30,
            min_profit_margin=1.5,
            peak_season_months=[10, 11, 12, 1, 2, 3, 4, 5, 6]
        ),
        "basketball_wnba": SportConfig(
            key="basketball_wnba", 
            title="WNBA",
            active=True,
            markets=["h2h", "spreads", "totals"],
            update_frequency=60,
            min_profit_margin=2.0,
            peak_season_months=[5, 6, 7, 8, 9, 10]
        ),
        "americanfootball_nfl": SportConfig(
            key="americanfootball_nfl",
            title="NFL", 
            active=True,
            markets=["h2h", "spreads", "totals"],
            update_frequency=45,
            min_profit_margin=1.0,
            peak_season_months=[9, 10, 11, 12, 1, 2]
        ),
        "baseball_mlb": SportConfig(
            key="baseball_mlb",
            title="MLB",
            active=True,
            markets=["h2h", "spreads", "totals"],
            update_frequency=120,
            min_profit_margin=1.5,
            peak_season_months=[4, 5, 6, 7, 8, 9, 10]
        ),
        "icehockey_nhl": SportConfig(
            key="icehockey_nhl",
            title="NHL",
            active=True,
            markets=["h2h", "spreads", "totals"],
            update_frequency=60,
            min_profit_margin=1.5,
            peak_season_months=[10, 11, 12, 1, 2, 3, 4, 5, 6]
        ),
        "soccer_usa_mls": SportConfig(
            key="soccer_usa_mls",
            title="MLS",
            active=True,
            markets=["h2h", "spreads", "totals"],
            update_frequency=90,
            min_profit_margin=2.0,
            peak_season_months=[3, 4, 5, 6, 7, 8, 9, 10, 11]
        )
    }
    
    @classmethod
    def get_sport_config(cls, sport_key: str) -> Optional[SportConfig]:
        """Get configuration for a specific sport"""
        return cls.SPORTS_CONFIG.get(sport_key)
    
    @classmethod
    def get_active_sports(cls) -> List[SportConfig]:
        """Get all active sports configurations"""
        return [config for config in cls.SPORTS_CONFIG.values() if config.active]
    
    @classmethod
    def get_all_sports(cls) -> Dict[str, SportConfig]:
        """Get all sports configurations"""
        return cls.SPORTS_CONFIG
    
    @classmethod
    def is_peak_season(cls, sport_key: str, month: int) -> bool:
        """Check if current month is peak season for sport"""
        config = cls.get_sport_config(sport_key)
        if not config:
            return False
        return month in config.peak_season_months
    
    @classmethod
    def get_update_frequency(cls, sport_key: str) -> int:
        """Get update frequency for sport (defaults to 60 seconds)"""
        config = cls.get_sport_config(sport_key)
        return config.update_frequency if config else 60