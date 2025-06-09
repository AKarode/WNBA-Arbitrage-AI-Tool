"""
Pytest configuration and fixtures for arbitrage detection tests

This module provides shared fixtures and configuration for all test modules,
including mock data, API responses, and test utilities.
"""

import pytest
import asyncio
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock
import json
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from app.main import app


# Test Client Fixture
@pytest.fixture
def test_client():
    """FastAPI test client for API endpoint testing"""
    return TestClient(app)


# Async event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Mock API Response Fixtures
@pytest.fixture
def mock_odds_api_response():
    """Mock response from The Odds API for single sport"""
    return {
        "sport_key": "basketball_wnba",
        "sport_title": "WNBA",
        "games": [
            {
                "id": "test_game_1",
                "sport_key": "basketball_wnba",
                "sport_title": "WNBA",
                "commence_time": "2025-06-10T02:00:00Z",
                "home_team": "Los Angeles Sparks",
                "away_team": "Golden State Valkyries",
                "bookmakers": [
                    {
                        "key": "fanduel",
                        "title": "FanDuel",
                        "last_update": "2025-06-09T07:41:09Z",
                        "markets": [
                            {
                                "key": "h2h",
                                "last_update": "2025-06-09T07:41:09Z",
                                "outcomes": [
                                    {"name": "Golden State Valkyries", "price": 3.05},
                                    {"name": "Los Angeles Sparks", "price": 1.38}
                                ]
                            },
                            {
                                "key": "spreads",
                                "last_update": "2025-06-09T07:41:09Z",
                                "outcomes": [
                                    {"name": "Golden State Valkyries", "price": 1.91, "point": 7.5},
                                    {"name": "Los Angeles Sparks", "price": 1.91, "point": -7.5}
                                ]
                            },
                            {
                                "key": "totals",
                                "last_update": "2025-06-09T07:41:09Z",
                                "outcomes": [
                                    {"name": "Over", "price": 1.91, "point": 165.5},
                                    {"name": "Under", "price": 1.91, "point": 165.5}
                                ]
                            }
                        ]
                    },
                    {
                        "key": "betonlineag",
                        "title": "BetOnline.ag",
                        "last_update": "2025-06-09T07:41:09Z",
                        "markets": [
                            {
                                "key": "h2h",
                                "last_update": "2025-06-09T07:41:09Z",
                                "outcomes": [
                                    {"name": "Golden State Valkyries", "price": 3.26},
                                    {"name": "Los Angeles Sparks", "price": 1.36}
                                ]
                            },
                            {
                                "key": "spreads",
                                "last_update": "2025-06-09T07:41:09Z",
                                "outcomes": [
                                    {"name": "Golden State Valkyries", "price": 1.95, "point": 7.5},
                                    {"name": "Los Angeles Sparks", "price": 1.87, "point": -7.5}
                                ]
                            },
                            {
                                "key": "totals",
                                "last_update": "2025-06-09T07:41:09Z",
                                "outcomes": [
                                    {"name": "Over", "price": 1.95, "point": 165.5},
                                    {"name": "Under", "price": 1.87, "point": 165.5}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }


@pytest.fixture
def arbitrage_opportunity_odds():
    """Mock odds data that contains a clear arbitrage opportunity"""
    return {
        "sport_key": "basketball_wnba",
        "sport_title": "WNBA",
        "games": [
            {
                "id": "arbitrage_game",
                "sport_key": "basketball_wnba",
                "sport_title": "WNBA",
                "commence_time": "2025-06-10T02:00:00Z",
                "home_team": "Team A",
                "away_team": "Team B",
                "bookmakers": [
                    {
                        "key": "bookmaker1",
                        "title": "Bookmaker 1",
                        "last_update": "2025-06-09T07:41:09Z",
                        "markets": [
                            {
                                "key": "h2h",
                                "last_update": "2025-06-09T07:41:09Z",
                                "outcomes": [
                                    {"name": "Team A", "price": 2.20},  # Implied prob: 45.45%
                                    {"name": "Team B", "price": 1.50}   # Implied prob: 66.67%
                                ]
                            }
                        ]
                    },
                    {
                        "key": "bookmaker2", 
                        "title": "Bookmaker 2",
                        "last_update": "2025-06-09T07:41:09Z",
                        "markets": [
                            {
                                "key": "h2h",
                                "last_update": "2025-06-09T07:41:09Z",
                                "outcomes": [
                                    {"name": "Team A", "price": 1.40},   # Implied prob: 71.43%
                                    {"name": "Team B", "price": 3.00}   # Implied prob: 33.33%
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    # Best odds: Team A at 2.20 (45.45%) + Team B at 3.00 (33.33%) = 78.78% total
    # Arbitrage profit: (1 - 0.7878) * 100 = 21.22%


@pytest.fixture
def multi_sport_odds_response():
    """Mock response for multiple sports scanning"""
    return {
        "basketball_wnba": {
            "games": [{"id": "wnba_game_1", "bookmakers": []}]
        },
        "basketball_nba": {
            "games": [{"id": "nba_game_1", "bookmakers": []}]
        },
        "americanfootball_nfl": {
            "games": [{"id": "nfl_game_1", "bookmakers": []}]
        }
    }


@pytest.fixture
def cross_market_arbitrage_odds():
    """Mock odds with cross-market arbitrage opportunities"""
    return {
        "sport_key": "basketball_wnba",
        "games": [
            {
                "id": "cross_market_game",
                "home_team": "Team A",
                "away_team": "Team B",
                "bookmakers": [
                    {
                        "key": "bookmaker1",
                        "title": "Bookmaker 1",
                        "markets": [
                            {
                                "key": "h2h",
                                "outcomes": [
                                    {"name": "Team A", "price": 1.90},
                                    {"name": "Team B", "price": 1.95}
                                ]
                            },
                            {
                                "key": "spreads",
                                "outcomes": [
                                    {"name": "Team A", "price": 2.10, "point": -2.5},
                                    {"name": "Team B", "price": 1.75, "point": 2.5}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }


# Mock API Client Fixtures
@pytest.fixture
def mock_odds_api_client():
    """Mock client for The Odds API"""
    mock_client = Mock()
    mock_client.get_sport_odds = AsyncMock()
    mock_client.get_all_sports_odds = AsyncMock()
    return mock_client


# Test Data Utilities
@pytest.fixture
def arbitrage_calculator():
    """Utility class for arbitrage calculations in tests"""
    class ArbitrageCalculator:
        @staticmethod
        def calculate_implied_probability(decimal_odds: float) -> float:
            """Calculate implied probability from decimal odds"""
            return 1 / decimal_odds
        
        @staticmethod
        def calculate_arbitrage_margin(outcomes: List[Dict[str, float]]) -> float:
            """Calculate arbitrage margin from list of best odds"""
            total_implied = sum(1 / outcome["price"] for outcome in outcomes)
            return (1 - total_implied) * 100 if total_implied < 1 else 0
        
        @staticmethod
        def calculate_stake_distribution(bankroll: float, outcomes: List[Dict[str, float]]) -> Dict[str, float]:
            """Calculate optimal stake distribution for arbitrage"""
            total_implied = sum(1 / outcome["price"] for outcome in outcomes)
            if total_implied >= 1:
                return {}
            
            stakes = {}
            for outcome in outcomes:
                implied_prob = 1 / outcome["price"]
                stake_percentage = implied_prob / total_implied
                stakes[outcome["name"]] = bankroll * stake_percentage
            
            return stakes
    
    return ArbitrageCalculator()


# Environment Variables for Testing
@pytest.fixture(autouse=True)
def test_environment(monkeypatch):
    """Set up test environment variables"""
    monkeypatch.setenv("ODDS_API_KEY", "test_api_key")
    monkeypatch.setenv("DEBUG", "True")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")


# Performance Testing Fixtures
@pytest.fixture
def performance_test_data():
    """Large dataset for performance testing"""
    games = []
    for i in range(100):  # 100 games for stress testing
        game = {
            "id": f"perf_test_game_{i}",
            "home_team": f"Home Team {i}",
            "away_team": f"Away Team {i}",
            "bookmakers": [
                {
                    "key": f"bookmaker_{j}",
                    "title": f"Bookmaker {j}",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": f"Home Team {i}", "price": 1.80 + (i % 10) * 0.1},
                                {"name": f"Away Team {i}", "price": 2.00 + (i % 8) * 0.1}
                            ]
                        }
                    ]
                }
                for j in range(5)  # 5 bookmakers per game
            ]
        }
        games.append(game)
    
    return {"games": games}


# Redis Mock for Caching Tests
@pytest.fixture
def mock_redis():
    """Mock Redis client for caching tests"""
    class MockRedis:
        def __init__(self):
            self.data = {}
        
        async def get(self, key):
            return self.data.get(key)
        
        async def set(self, key, value, ex=None):
            self.data[key] = value
        
        async def delete(self, key):
            self.data.pop(key, None)
        
        async def exists(self, key):
            return key in self.data
    
    return MockRedis()