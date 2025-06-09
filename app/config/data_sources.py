"""
WNBA Arbitrage AI Tool - Data Sources Configuration
Configuration for all data sources and ingestion parameters
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class SourceConfig:
    """Configuration for individual data sources"""
    name: str
    enabled: bool
    rate_limit_per_minute: float
    rate_limit_per_day: int
    priority: int  # 1 = highest priority
    timeout: int
    retry_attempts: int
    retry_delay: int

@dataclass
class ScrapingConfig:
    """Configuration for web scraping"""
    user_agents: List[str]
    proxy_enabled: bool
    proxy_rotation: bool
    captcha_service: str
    request_delay_min: int
    request_delay_max: int
    headless_browser: bool

# Data source configurations
DATA_SOURCES = {
    'odds_api': SourceConfig(
        name='The Odds API',
        enabled=bool(os.getenv('ODDS_API_KEY')),
        rate_limit_per_minute=60,
        rate_limit_per_day=500,  # Free tier limit
        priority=1,
        timeout=30,
        retry_attempts=3,
        retry_delay=5
    ),
    
    'bovada_scraper': SourceConfig(
        name='Bovada Scraper',
        enabled=True,
        rate_limit_per_minute=0.5,  # Every 2 minutes
        rate_limit_per_day=720,
        priority=2,
        timeout=45,
        retry_attempts=2,
        retry_delay=10
    ),
    
    'betonline_scraper': SourceConfig(
        name='BetOnline Scraper',
        enabled=True,
        rate_limit_per_minute=1.0,  # Every minute
        rate_limit_per_day=1440,
        priority=3,
        timeout=60,
        retry_attempts=2,
        retry_delay=15
    ),
    
    'mybookie_scraper': SourceConfig(
        name='MyBookie Scraper',
        enabled=False,  # To be implemented
        rate_limit_per_minute=0.75,
        rate_limit_per_day=1080,
        priority=4,
        timeout=45,
        retry_attempts=2,
        retry_delay=12
    )
}

# Scraping configuration
SCRAPING_CONFIG = ScrapingConfig(
    user_agents=[
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ],
    proxy_enabled=False,  # Enable in production
    proxy_rotation=False,
    captcha_service='2captcha',  # For Bovada if needed
    request_delay_min=2,
    request_delay_max=8,
    headless_browser=True
)

# Market mappings for different sources
MARKET_MAPPINGS = {
    'bovada': {
        'moneyline': 'h2h',
        'match result': 'h2h',
        'spread': 'spreads',
        'handicap': 'spreads',
        'total': 'totals',
        'over/under': 'totals'
    },
    'betonline': {
        'money line': 'h2h',
        'point spread': 'spreads',
        'game total': 'totals'
    },
    'mybookie': {
        'moneyline': 'h2h',
        'spread': 'spreads',
        'total': 'totals'
    }
}

# Cache configuration
CACHE_CONFIG = {
    'odds_ttl': 60,           # Cache odds for 1 minute
    'arbitrage_ttl': 30,      # Cache arbitrage calculations for 30 seconds
    'news_ttl': 300,          # Cache news for 5 minutes
    'health_ttl': 120,        # Cache health checks for 2 minutes
    'rate_limit_ttl': 3600,   # Track rate limits for 1 hour
}

# Arbitrage detection settings
ARBITRAGE_CONFIG = {
    'min_profit_margin': 0.01,        # 1% minimum profit
    'max_profit_margin': 0.20,        # 20% maximum (likely error)
    'min_bookmakers': 2,              # Minimum sources required
    'max_stake': 10000,               # Maximum recommended stake
    'execution_window': 600,          # 10 minutes estimated execution window
    'confidence_threshold': 0.85,     # 85% confidence required
}

# Alert thresholds
ALERT_THRESHOLDS = {
    'high_profit': 0.05,      # 5%+ profit opportunities
    'medium_profit': 0.03,    # 3%+ profit opportunities  
    'low_profit': 0.015,      # 1.5%+ profit opportunities
    'immediate_alert': 0.04,  # 4%+ triggers immediate notification
}

# Data quality settings
DATA_QUALITY_CONFIG = {
    'max_odds_age': 300,              # 5 minutes max age for odds
    'min_sources_for_arbitrage': 2,   # Minimum sources for valid arbitrage
    'outlier_detection': True,        # Enable outlier detection
    'max_price_deviation': 0.50,      # 50% max deviation from market
}

# Development vs Production settings
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    # Production settings - more aggressive data collection
    DATA_SOURCES['bovada_scraper'].rate_limit_per_minute = 1.0
    DATA_SOURCES['betonline_scraper'].rate_limit_per_minute = 2.0
    SCRAPING_CONFIG.proxy_enabled = True
    SCRAPING_CONFIG.proxy_rotation = True
    CACHE_CONFIG['odds_ttl'] = 30  # Cache for only 30 seconds
elif ENVIRONMENT == 'staging':
    # Staging settings - moderate collection
    DATA_SOURCES['bovada_scraper'].rate_limit_per_minute = 0.75
    CACHE_CONFIG['odds_ttl'] = 45
else:
    # Development settings - conservative collection
    # Use default settings defined above
    pass

# Export configuration
def get_source_config(source_name: str) -> SourceConfig:
    """Get configuration for a specific source"""
    return DATA_SOURCES.get(source_name)

def get_enabled_sources() -> List[str]:
    """Get list of enabled data sources"""
    return [name for name, config in DATA_SOURCES.items() if config.enabled]

def get_cache_ttl(cache_type: str) -> int:
    """Get TTL for specific cache type"""
    return CACHE_CONFIG.get(cache_type, 60)

def get_arbitrage_settings() -> Dict[str, Any]:
    """Get arbitrage detection settings"""
    return ARBITRAGE_CONFIG

def get_alert_thresholds() -> Dict[str, float]:
    """Get alert threshold settings"""
    return ALERT_THRESHOLDS

# Validation functions
def validate_profit_margin(margin: float) -> bool:
    """Validate if profit margin is within acceptable bounds"""
    return ARBITRAGE_CONFIG['min_profit_margin'] <= margin <= ARBITRAGE_CONFIG['max_profit_margin']

def is_odds_data_fresh(timestamp: str) -> bool:
    """Check if odds data is fresh enough for arbitrage detection"""
    from datetime import datetime, timezone
    import dateutil.parser
    
    try:
        odds_time = dateutil.parser.parse(timestamp)
        current_time = datetime.now(timezone.utc)
        age_seconds = (current_time - odds_time).total_seconds()
        return age_seconds <= DATA_QUALITY_CONFIG['max_odds_age']
    except:
        return False

# Market configuration for different sports (future expansion)
SPORT_CONFIGS = {
    'basketball_wnba': {
        'season_months': [5, 6, 7, 8, 9, 10],  # May through October
        'peak_hours': [19, 20, 21, 22],         # 7-10 PM ET
        'game_duration': 120,                   # 2 hours average
        'update_frequency': {
            'pre_game': 300,    # 5 minutes before games
            'live_game': 30,    # 30 seconds during games
            'off_season': 3600  # 1 hour during off-season
        }
    }
}

def get_sport_config(sport_key: str) -> Dict[str, Any]:
    """Get configuration for specific sport"""
    return SPORT_CONFIGS.get(sport_key, {})

def is_peak_season(sport_key: str = 'basketball_wnba') -> bool:
    """Check if current time is during peak season"""
    import datetime
    current_month = datetime.datetime.now().month
    sport_config = get_sport_config(sport_key)
    return current_month in sport_config.get('season_months', [])

def get_update_frequency(sport_key: str = 'basketball_wnba', context: str = 'pre_game') -> int:
    """Get recommended update frequency based on context"""
    sport_config = get_sport_config(sport_key)
    return sport_config.get('update_frequency', {}).get(context, 300)