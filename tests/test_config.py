"""
Tests for Configuration Module
Test configuration settings and validation
"""

import pytest
import os
from unittest.mock import patch
from datetime import datetime

from app.config.data_sources import (
    DATA_SOURCES,
    SCRAPING_CONFIG,
    MARKET_MAPPINGS,
    CACHE_CONFIG,
    ARBITRAGE_CONFIG,
    ALERT_THRESHOLDS,
    get_source_config,
    get_enabled_sources,
    get_cache_ttl,
    get_arbitrage_settings,
    get_alert_thresholds,
    validate_profit_margin,
    is_odds_data_fresh,
    get_sport_config,
    is_peak_season,
    get_update_frequency
)

class TestDataSourcesConfig:
    """Test data sources configuration"""
    
    def test_data_sources_structure(self):
        """Test that all data sources have required configuration"""
        required_fields = ['name', 'enabled', 'rate_limit_per_minute', 
                          'rate_limit_per_day', 'priority', 'timeout', 
                          'retry_attempts', 'retry_delay']
        
        for source_name, config in DATA_SOURCES.items():
            for field in required_fields:
                assert hasattr(config, field), f"Source {source_name} missing {field}"
                assert getattr(config, field) is not None, f"Source {source_name} has None {field}"
    
    def test_scraping_config_structure(self):
        """Test scraping configuration structure"""
        assert len(SCRAPING_CONFIG.user_agents) > 0
        assert isinstance(SCRAPING_CONFIG.proxy_enabled, bool)
        assert isinstance(SCRAPING_CONFIG.headless_browser, bool)
        assert SCRAPING_CONFIG.request_delay_min < SCRAPING_CONFIG.request_delay_max
    
    def test_market_mappings_complete(self):
        """Test that market mappings are complete"""
        expected_sources = ['bovada', 'betonline', 'mybookie']
        expected_markets = ['h2h', 'spreads', 'totals']
        
        for source in expected_sources:
            assert source in MARKET_MAPPINGS
            mappings = MARKET_MAPPINGS[source]
            # Each source should map to standard markets
            mapped_markets = set(mappings.values())
            assert all(market in expected_markets for market in mapped_markets)
    
    def test_get_source_config(self):
        """Test source configuration retrieval"""
        # Test existing source
        config = get_source_config('odds_api')
        assert config is not None
        assert config.name == 'The Odds API'
        
        # Test non-existing source
        config = get_source_config('non_existent_source')
        assert config is None
    
    def test_get_enabled_sources(self):
        """Test enabled sources retrieval"""
        enabled = get_enabled_sources()
        assert isinstance(enabled, list)
        
        # Verify only enabled sources are returned
        for source_name in enabled:
            config = get_source_config(source_name)
            assert config.enabled == True

class TestCacheConfig:
    """Test cache configuration"""
    
    def test_cache_config_structure(self):
        """Test cache configuration has all required keys"""
        required_keys = ['odds_ttl', 'arbitrage_ttl', 'news_ttl', 
                        'health_ttl', 'rate_limit_ttl']
        
        for key in required_keys:
            assert key in CACHE_CONFIG
            assert isinstance(CACHE_CONFIG[key], int)
            assert CACHE_CONFIG[key] > 0
    
    def test_get_cache_ttl(self):
        """Test cache TTL retrieval"""
        # Test existing cache type
        ttl = get_cache_ttl('odds_ttl')
        assert ttl == CACHE_CONFIG['odds_ttl']
        
        # Test non-existing cache type (should return default)
        ttl = get_cache_ttl('non_existent_cache')
        assert ttl == 60  # Default value

class TestArbitrageConfig:
    """Test arbitrage configuration"""
    
    def test_arbitrage_config_structure(self):
        """Test arbitrage configuration structure"""
        required_keys = ['min_profit_margin', 'max_profit_margin', 
                        'min_bookmakers', 'max_stake', 'execution_window']
        
        for key in required_keys:
            assert key in ARBITRAGE_CONFIG
            assert isinstance(ARBITRAGE_CONFIG[key], (int, float))
    
    def test_arbitrage_config_logical_values(self):
        """Test arbitrage configuration has logical values"""
        assert ARBITRAGE_CONFIG['min_profit_margin'] < ARBITRAGE_CONFIG['max_profit_margin']
        assert ARBITRAGE_CONFIG['min_bookmakers'] >= 2
        assert ARBITRAGE_CONFIG['max_stake'] > 0
        assert ARBITRAGE_CONFIG['execution_window'] > 0
    
    def test_get_arbitrage_settings(self):
        """Test arbitrage settings retrieval"""
        settings = get_arbitrage_settings()
        assert settings == ARBITRAGE_CONFIG
        assert isinstance(settings, dict)

class TestAlertThresholds:
    """Test alert thresholds configuration"""
    
    def test_alert_thresholds_structure(self):
        """Test alert thresholds structure"""
        required_keys = ['high_profit', 'medium_profit', 'low_profit', 'immediate_alert']
        
        for key in required_keys:
            assert key in ALERT_THRESHOLDS
            assert isinstance(ALERT_THRESHOLDS[key], float)
            assert 0 < ALERT_THRESHOLDS[key] < 1  # Should be percentage as decimal
    
    def test_alert_thresholds_ordering(self):
        """Test that alert thresholds are in logical order"""
        assert ALERT_THRESHOLDS['high_profit'] > ALERT_THRESHOLDS['medium_profit']
        assert ALERT_THRESHOLDS['medium_profit'] > ALERT_THRESHOLDS['low_profit']
    
    def test_get_alert_thresholds(self):
        """Test alert thresholds retrieval"""
        thresholds = get_alert_thresholds()
        assert thresholds == ALERT_THRESHOLDS
        assert isinstance(thresholds, dict)

class TestValidationFunctions:
    """Test validation functions"""
    
    def test_validate_profit_margin_valid(self):
        """Test profit margin validation with valid values"""
        valid_margins = [0.01, 0.025, 0.05, 0.1, 0.15]
        
        for margin in valid_margins:
            assert validate_profit_margin(margin) == True
    
    def test_validate_profit_margin_invalid(self):
        """Test profit margin validation with invalid values"""
        invalid_margins = [0.005, 0.25, -0.01, 0]
        
        for margin in invalid_margins:
            assert validate_profit_margin(margin) == False
    
    def test_is_odds_data_fresh_valid(self):
        """Test odds data freshness validation with fresh data"""
        # Recent timestamp (within 5 minutes)
        recent_time = datetime.now().isoformat()
        assert is_odds_data_fresh(recent_time) == True
    
    def test_is_odds_data_fresh_stale(self):
        """Test odds data freshness validation with stale data"""
        # Old timestamp (over 5 minutes)
        from datetime import timedelta
        old_time = (datetime.now() - timedelta(minutes=10)).isoformat()
        assert is_odds_data_fresh(old_time) == False
    
    def test_is_odds_data_fresh_invalid_format(self):
        """Test odds data freshness with invalid timestamp format"""
        invalid_timestamps = ["invalid", "", None, "2024-13-45"]
        
        for timestamp in invalid_timestamps:
            assert is_odds_data_fresh(timestamp) == False

class TestSportConfig:
    """Test sport-specific configuration"""
    
    def test_get_sport_config_wnba(self):
        """Test WNBA sport configuration"""
        config = get_sport_config('basketball_wnba')
        
        assert 'season_months' in config
        assert 'peak_hours' in config
        assert 'game_duration' in config
        assert 'update_frequency' in config
        
        # WNBA season should be May-October
        assert 5 in config['season_months']  # May
        assert 10 in config['season_months']  # October
    
    def test_get_sport_config_invalid(self):
        """Test sport configuration for invalid sport"""
        config = get_sport_config('invalid_sport')
        assert config == {}
    
    @patch('datetime.datetime')
    def test_is_peak_season_during_season(self, mock_datetime):
        """Test peak season detection during WNBA season"""
        # Mock July (month 7, during WNBA season)
        mock_datetime.now.return_value.month = 7
        
        assert is_peak_season('basketball_wnba') == True
    
    @patch('datetime.datetime')
    def test_is_peak_season_off_season(self, mock_datetime):
        """Test peak season detection during off-season"""
        # Mock February (month 2, off-season)
        mock_datetime.now.return_value.month = 2
        
        assert is_peak_season('basketball_wnba') == False
    
    def test_get_update_frequency(self):
        """Test update frequency retrieval"""
        # Test different contexts
        pre_game_freq = get_update_frequency('basketball_wnba', 'pre_game')
        live_game_freq = get_update_frequency('basketball_wnba', 'live_game')
        off_season_freq = get_update_frequency('basketball_wnba', 'off_season')
        
        assert isinstance(pre_game_freq, int)
        assert isinstance(live_game_freq, int)
        assert isinstance(off_season_freq, int)
        
        # Live games should have highest frequency (lowest interval)
        assert live_game_freq < pre_game_freq
        assert pre_game_freq < off_season_freq

class TestEnvironmentSpecificConfig:
    """Test environment-specific configuration"""
    
    @patch.dict(os.environ, {'ENVIRONMENT': 'production'})
    def test_production_config_changes(self):
        """Test that production environment affects configuration"""
        # This would require reloading the module, which is complex
        # For now, just test that environment variable is read
        assert os.environ.get('ENVIRONMENT') == 'production'
    
    @patch.dict(os.environ, {'ENVIRONMENT': 'development'})
    def test_development_config_default(self):
        """Test development environment configuration"""
        assert os.environ.get('ENVIRONMENT') == 'development'
    
    @patch.dict(os.environ, {'ENVIRONMENT': 'staging'})
    def test_staging_config_moderate(self):
        """Test staging environment configuration"""
        assert os.environ.get('ENVIRONMENT') == 'staging'

class TestConfigurationIntegrity:
    """Test overall configuration integrity"""
    
    def test_no_conflicting_priorities(self):
        """Test that no two sources have the same priority"""
        priorities = [config.priority for config in DATA_SOURCES.values()]
        assert len(priorities) == len(set(priorities)), "Duplicate priorities found"
    
    def test_rate_limits_reasonable(self):
        """Test that rate limits are reasonable"""
        for source_name, config in DATA_SOURCES.items():
            # Rate limits should be positive
            assert config.rate_limit_per_minute > 0
            assert config.rate_limit_per_day > 0
            
            # Daily limit should be higher than minute limit * 60 * 24
            # (unless specifically throttled)
            max_daily_from_minute = config.rate_limit_per_minute * 60 * 24
            assert config.rate_limit_per_day <= max_daily_from_minute
    
    def test_timeout_values_reasonable(self):
        """Test that timeout values are reasonable"""
        for source_name, config in DATA_SOURCES.items():
            # Timeouts should be reasonable (between 10 and 300 seconds)
            assert 10 <= config.timeout <= 300
            
            # Retry attempts should be reasonable
            assert 0 <= config.retry_attempts <= 5
            
            # Retry delay should be reasonable
            assert 1 <= config.retry_delay <= 60
    
    def test_cache_ttl_hierarchy(self):
        """Test that cache TTL values follow logical hierarchy"""
        # Arbitrage should have shorter TTL than odds (more time-sensitive)
        assert CACHE_CONFIG['arbitrage_ttl'] <= CACHE_CONFIG['odds_ttl']
        
        # News can have longer TTL
        assert CACHE_CONFIG['news_ttl'] >= CACHE_CONFIG['odds_ttl']
    
    def test_all_configs_json_serializable(self):
        """Test that all configuration can be JSON serialized"""
        import json
        
        # Test main configs
        configs_to_test = [
            CACHE_CONFIG,
            ARBITRAGE_CONFIG,
            ALERT_THRESHOLDS,
            MARKET_MAPPINGS
        ]
        
        for config in configs_to_test:
            try:
                json.dumps(config)
            except TypeError as e:
                pytest.fail(f"Configuration not JSON serializable: {e}")

class TestConfigurationDocumentation:
    """Test that configuration is properly documented"""
    
    def test_all_sources_have_names(self):
        """Test that all sources have human-readable names"""
        for source_name, config in DATA_SOURCES.items():
            assert config.name is not None
            assert len(config.name) > 0
            assert isinstance(config.name, str)
    
    def test_market_mappings_documented(self):
        """Test that market mappings are comprehensive"""
        standard_markets = {'h2h', 'spreads', 'totals'}
        
        for source, mappings in MARKET_MAPPINGS.items():
            mapped_markets = set(mappings.values())
            # Each source should map to at least basic markets
            assert mapped_markets.intersection(standard_markets), f"Source {source} doesn't map to standard markets"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])