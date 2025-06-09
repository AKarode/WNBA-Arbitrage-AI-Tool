"""
Pytest Configuration and Shared Fixtures
Global test configuration for the WNBA Arbitrage AI Tool
"""

import pytest
import asyncio
import json
import os
import redis
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from typing import Dict, List, Any

# Import app and modules for testing
from app.main import app
from app.services.multi_source_ingestion import (
    OddsData,
    ArbitrageOpportunity,
    RateLimitManager,
    MultiSourceDataAggregator
)
from app.config.data_sources import DATA_SOURCES

# Set test environment
os.environ['ENVIRONMENT'] = 'testing'

# Global test fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_client():
    """FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    mock_client = Mock(spec=redis.Redis)
    mock_client.ping.return_value = True
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.setex.return_value = True
    mock_client.incr.return_value = 1
    mock_client.expire.return_value = True
    mock_client.delete.return_value = 1
    mock_client.flushdb.return_value = True
    
    # Mock pipeline
    mock_pipeline = Mock()
    mock_pipeline.incr.return_value = mock_pipeline
    mock_pipeline.expire.return_value = mock_pipeline
    mock_pipeline.execute.return_value = [1, True, 1, True]
    mock_client.pipeline.return_value = mock_pipeline
    
    return mock_client

@pytest.fixture
def rate_limiter(mock_redis):
    """Rate limiter with mocked Redis for testing"""
    with patch('app.services.multi_source_ingestion.redis.Redis', return_value=mock_redis):
        return RateLimitManager(mock_redis)

@pytest.fixture
def sample_odds_data() -> List[OddsData]:
    """Sample odds data for testing"""
    return [
        OddsData(
            game_id="fixture_game_1",
            home_team="Las Vegas Aces",
            away_team="New York Liberty",
            commence_time="2024-07-15T19:00:00Z",
            bookmaker="bovada",
            market_type="h2h",
            outcomes=[
                {"name": "Las Vegas Aces", "price": -140},
                {"name": "New York Liberty", "price": 120}
            ],
            last_update="2024-07-15T18:30:00Z",
            source="bovada_scraper"
        ),
        OddsData(
            game_id="fixture_game_1",
            home_team="Las Vegas Aces",
            away_team="New York Liberty",
            commence_time="2024-07-15T19:00:00Z",
            bookmaker="betonline",
            market_type="h2h",
            outcomes=[
                {"name": "Las Vegas Aces", "price": -130},
                {"name": "New York Liberty", "price": 110}
            ],
            last_update="2024-07-15T18:25:00Z",
            source="betonline_scraper"
        ),
        OddsData(
            game_id="fixture_game_2",
            home_team="Seattle Storm",
            away_team="Phoenix Mercury",
            commence_time="2024-07-15T21:00:00Z",
            bookmaker="bovada",
            market_type="spreads",
            outcomes=[
                {"name": "Seattle Storm", "price": -110, "point": -3.5},
                {"name": "Phoenix Mercury", "price": -110, "point": 3.5}
            ],
            last_update="2024-07-15T18:30:00Z",
            source="bovada_scraper"
        )
    ]

@pytest.fixture
def sample_arbitrage_opportunity() -> ArbitrageOpportunity:
    """Sample arbitrage opportunity for testing"""
    return ArbitrageOpportunity(
        game_id="fixture_game_1",
        game_description="New York Liberty @ Las Vegas Aces",
        market_type="h2h",
        profit_margin=0.025,
        profit_percentage=2.5,
        best_odds={
            "Las Vegas Aces": {
                "price": -130,
                "bookmaker": "betonline",
                "source": "betonline_scraper"
            },
            "New York Liberty": {
                "price": 120,
                "bookmaker": "bovada",
                "source": "bovada_scraper"
            }
        },
        total_stake=1000,
        individual_stakes={
            "Las Vegas Aces": 565.22,
            "New York Liberty": 434.78
        },
        detected_at=datetime.now(timezone.utc).isoformat(),
        expiry_estimate=(datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    )

@pytest.fixture
def sample_odds_api_response() -> List[Dict]:
    """Sample response from The Odds API"""
    return [
        {
            'id': 'odds_api_game_123',
            'sport_key': 'basketball_wnba',
            'sport_title': 'WNBA',
            'commence_time': '2024-07-15T19:00:00Z',
            'home_team': 'Las Vegas Aces',
            'away_team': 'New York Liberty',
            'bookmakers': [
                {
                    'key': 'bovada',
                    'title': 'Bovada',
                    'last_update': '2024-07-15T18:30:00Z',
                    'markets': [
                        {
                            'key': 'h2h',
                            'last_update': '2024-07-15T18:30:00Z',
                            'outcomes': [
                                {'name': 'Las Vegas Aces', 'price': -140},
                                {'name': 'New York Liberty', 'price': 120}
                            ]
                        },
                        {
                            'key': 'spreads',
                            'last_update': '2024-07-15T18:30:00Z',
                            'outcomes': [
                                {'name': 'Las Vegas Aces', 'price': -110, 'point': -2.5},
                                {'name': 'New York Liberty', 'price': -110, 'point': 2.5}
                            ]
                        }
                    ]
                }
            ]
        }
    ]

@pytest.fixture
def sample_bovada_response() -> Dict:
    """Sample response from Bovada scraping"""
    return {
        'events': [
            {
                'id': 'bovada_game_456',
                'startTime': '2024-07-15T19:00:00Z',
                'competitors': [
                    {'name': 'Las Vegas Aces'},
                    {'name': 'New York Liberty'}
                ],
                'displayGroups': [
                    {
                        'description': 'Moneyline',
                        'markets': [
                            {
                                'outcomes': [
                                    {
                                        'description': 'Las Vegas Aces',
                                        'price': {'american': -145}
                                    },
                                    {
                                        'description': 'New York Liberty',
                                        'price': {'american': 125}
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'description': 'Spread',
                        'markets': [
                            {
                                'outcomes': [
                                    {
                                        'description': 'Las Vegas Aces',
                                        'price': {'american': -110, 'handicap': -2.5}
                                    },
                                    {
                                        'description': 'New York Liberty',
                                        'price': {'american': -110, 'handicap': 2.5}
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }

@pytest.fixture
def multi_source_odds_data(sample_odds_data) -> Dict[str, List[OddsData]]:
    """Multi-source odds data for testing"""
    return {
        'bovada_scraper': [sample_odds_data[0], sample_odds_data[2]],
        'betonline_scraper': [sample_odds_data[1]],
        'odds_api': []
    }

@pytest.fixture
def multiple_arbitrage_opportunities(sample_arbitrage_opportunity) -> List[ArbitrageOpportunity]:
    """Multiple arbitrage opportunities for testing"""
    opportunities = [sample_arbitrage_opportunity]
    
    # Add a second opportunity
    opportunity_2 = ArbitrageOpportunity(
        game_id="fixture_game_2",
        game_description="Phoenix Mercury @ Seattle Storm",
        market_type="spreads",
        profit_margin=0.035,
        profit_percentage=3.5,
        best_odds={
            "Seattle Storm": {
                "price": -105,
                "bookmaker": "bovada",
                "source": "bovada_scraper"
            },
            "Phoenix Mercury": {
                "price": -115,
                "bookmaker": "betonline",
                "source": "betonline_scraper"
            }
        },
        total_stake=1000,
        individual_stakes={
            "Seattle Storm": 512.20,
            "Phoenix Mercury": 487.80
        },
        detected_at=datetime.now(timezone.utc).isoformat(),
        expiry_estimate=(datetime.now(timezone.utc) + timedelta(minutes=8)).isoformat()
    )
    opportunities.append(opportunity_2)
    
    return opportunities

@pytest.fixture
def mock_aiohttp_response():
    """Mock aiohttp response for testing"""
    async def _mock_response(status=200, json_data=None, text_data=None):
        mock_resp = AsyncMock()
        mock_resp.status = status
        if json_data is not None:
            mock_resp.json.return_value = json_data
        if text_data is not None:
            mock_resp.text.return_value = text_data
        return mock_resp
    return _mock_response

@pytest.fixture
def mock_selenium_driver():
    """Mock Selenium WebDriver for testing"""
    mock_driver = Mock()
    mock_driver.get.return_value = None
    mock_driver.quit.return_value = None
    mock_driver.page_source = '<html><body>Test HTML</body></html>'
    return mock_driver

# Test data generators
@pytest.fixture
def odds_data_generator():
    """Generator for creating test odds data"""
    def _generate_odds(
        game_id: str = "test_game",
        home_team: str = "Home Team",
        away_team: str = "Away Team",
        bookmaker: str = "test_book",
        source: str = "test_source",
        market_type: str = "h2h",
        home_price: int = -110,
        away_price: int = -110
    ) -> OddsData:
        return OddsData(
            game_id=game_id,
            home_team=home_team,
            away_team=away_team,
            commence_time=datetime.now(timezone.utc).isoformat(),
            bookmaker=bookmaker,
            market_type=market_type,
            outcomes=[
                {"name": home_team, "price": home_price},
                {"name": away_team, "price": away_price}
            ],
            last_update=datetime.now(timezone.utc).isoformat(),
            source=source
        )
    return _generate_odds

@pytest.fixture
def arbitrage_opportunity_generator():
    """Generator for creating test arbitrage opportunities"""
    def _generate_arbitrage(
        game_id: str = "test_game",
        game_description: str = "Away @ Home",
        profit_percentage: float = 2.5,
        market_type: str = "h2h"
    ) -> ArbitrageOpportunity:
        return ArbitrageOpportunity(
            game_id=game_id,
            game_description=game_description,
            market_type=market_type,
            profit_margin=profit_percentage / 100,
            profit_percentage=profit_percentage,
            best_odds={
                "Team A": {"price": -130, "bookmaker": "book1", "source": "source1"},
                "Team B": {"price": 120, "bookmaker": "book2", "source": "source2"}
            },
            total_stake=1000,
            individual_stakes={"Team A": 500, "Team B": 500},
            detected_at=datetime.now(timezone.utc).isoformat(),
            expiry_estimate=(datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
        )
    return _generate_arbitrage

# Test environment configuration
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables"""
    test_env_vars = {
        'ENVIRONMENT': 'testing',
        'REDIS_URL': 'redis://localhost:6379/15',  # Test database
        'ODDS_API_KEY': 'test_api_key_for_testing',
        'DEBUG': 'true'
    }
    
    # Store original values
    original_values = {}
    for key, value in test_env_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original values
    for key, original_value in original_values.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value

# Database fixtures (for future use)
@pytest.fixture
def mock_database():
    """Mock database connection for testing"""
    mock_db = Mock()
    mock_db.execute.return_value = Mock()
    mock_db.fetchall.return_value = []
    mock_db.fetchone.return_value = None
    mock_db.commit.return_value = None
    mock_db.rollback.return_value = None
    mock_db.close.return_value = None
    return mock_db

# Performance testing fixtures
@pytest.fixture
def performance_timer():
    """Timer for performance testing"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()

# Async test helpers
@pytest.fixture
def async_mock():
    """Helper for creating async mocks"""
    def _async_mock(return_value=None, side_effect=None):
        mock = AsyncMock()
        if return_value is not None:
            mock.return_value = return_value
        if side_effect is not None:
            mock.side_effect = side_effect
        return mock
    return _async_mock

# Test markers for pytest
def pytest_configure(config):
    """Configure pytest markers"""
    markers = [
        "slow: marks tests as slow (deselect with '-m \"not slow\"')",
        "integration: marks tests as integration tests",
        "unit: marks tests as unit tests",
        "api: marks tests as API tests",
        "scraping: marks tests requiring web scraping",
        "redis: marks tests requiring Redis",
        "performance: marks tests for performance validation"
    ]
    
    for marker in markers:
        config.addinivalue_line("markers", marker)

# Cleanup fixtures
@pytest.fixture
def cleanup_redis(mock_redis):
    """Cleanup Redis data after tests"""
    yield mock_redis
    # In real tests with actual Redis, you would flush the test database
    # mock_redis.flushdb()

@pytest.fixture
def cleanup_files():
    """Cleanup test files after tests"""
    test_files = []
    
    def _add_file(filepath):
        test_files.append(filepath)
    
    yield _add_file
    
    # Cleanup
    for filepath in test_files:
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass  # Ignore cleanup errors

# Error simulation fixtures
@pytest.fixture
def error_simulator():
    """Simulate various error conditions"""
    class ErrorSimulator:
        @staticmethod
        def network_error():
            import aiohttp
            return aiohttp.ClientError("Network error")
        
        @staticmethod
        def timeout_error():
            import asyncio
            return asyncio.TimeoutError("Request timeout")
        
        @staticmethod
        def redis_error():
            return redis.RedisError("Redis connection failed")
        
        @staticmethod
        def json_error():
            return json.JSONDecodeError("Invalid JSON", "", 0)
        
        @staticmethod
        def selenium_error():
            from selenium.common.exceptions import WebDriverException
            return WebDriverException("WebDriver error")
    
    return ErrorSimulator()

# Configuration for specific test types
@pytest.fixture
def api_test_config():
    """Configuration for API tests"""
    return {
        'base_url': 'http://testserver',
        'timeout': 30,
        'headers': {'Content-Type': 'application/json'}
    }

@pytest.fixture
def scraping_test_config():
    """Configuration for scraping tests"""
    return {
        'user_agent': 'Mozilla/5.0 (Test Browser)',
        'timeout': 10,
        'retry_attempts': 2
    }

# Parametrized fixtures for comprehensive testing
@pytest.fixture(params=['bovada', 'betonline', 'mybookie'])
def bookmaker_name(request):
    """Parametrized bookmaker names for testing"""
    return request.param

@pytest.fixture(params=['h2h', 'spreads', 'totals'])
def market_type(request):
    """Parametrized market types for testing"""
    return request.param

@pytest.fixture(params=[0.01, 0.025, 0.05, 0.1])
def profit_margin(request):
    """Parametrized profit margins for testing"""
    return request.param