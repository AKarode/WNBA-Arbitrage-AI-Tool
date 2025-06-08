"""
Tests for WNBA Arbitrage AI Tool - Odds API Service
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.odds_api import (
    TheOddsAPI, 
    OddsAggregator, 
    OddsAPIError,
    get_wnba_odds,
    find_arbitrage_opportunities,
    get_provider_status
)

client = TestClient(app)


class TestOddsAPI:
    """Test The Odds API service class"""
    
    def test_init_without_api_key(self):
        """Test initialization without API key raises error"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(OddsAPIError, match="API key not found"):
                TheOddsAPI()
    
    def test_init_with_api_key(self):
        """Test successful initialization with API key"""
        with patch.dict(os.environ, {'ODDS_API_KEY': 'test_key'}):
            api = TheOddsAPI()
            assert api.api_key == 'test_key'
            assert api.sport_key == 'basketball_wnba'
            assert 'us' in api.regions
    
    @patch('app.services.odds_api.requests.get')
    def test_get_wnba_odds_success(self, mock_get):
        """Test successful WNBA odds retrieval"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                'id': 'test_game_1',
                'sport_key': 'basketball_wnba',
                'sport_title': 'WNBA',
                'commence_time': '2024-07-15T19:00:00Z',
                'home_team': 'Las Vegas Aces',
                'away_team': 'New York Liberty',
                'bookmakers': [
                    {
                        'key': 'fanduel',
                        'title': 'FanDuel',
                        'markets': [
                            {
                                'key': 'h2h',
                                'last_update': '2024-07-15T18:00:00Z',
                                'outcomes': [
                                    {'name': 'Las Vegas Aces', 'price': -110},
                                    {'name': 'New York Liberty', 'price': +100}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {'ODDS_API_KEY': 'test_key'}):
            api = TheOddsAPI()
            result = api.get_wnba_odds()
            
            assert result['source'] == 'the_odds_api'
            assert result['total_games'] == 1
            assert result['sport'] == 'basketball_wnba'
            assert 'data' in result
            assert len(result['data']) == 1
    
    def test_american_odds_conversion(self):
        """Test American odds conversion logic"""
        # Positive odds: +150 should give implied probability of 100/(150+100) = 0.4
        positive_odds = 150
        implied_prob_pos = 100 / (positive_odds + 100)
        assert abs(implied_prob_pos - 0.4) < 0.001
        
        # Negative odds: -200 should give implied probability of 200/(200+100) = 0.667
        negative_odds = -200
        implied_prob_neg = abs(negative_odds) / (abs(negative_odds) + 100)
        assert abs(implied_prob_neg - 0.667) < 0.001


class TestOddsAggregator:
    """Test the OddsAggregator service class"""
    
    def test_initialization(self):
        """Test aggregator initialization"""
        aggregator = OddsAggregator()
        assert hasattr(aggregator, 'providers')
        assert isinstance(aggregator.providers, dict)
    
    @patch('app.services.odds_api.os.getenv')
    def test_provider_initialization_without_key(self, mock_getenv):
        """Test provider initialization without API key"""
        mock_getenv.return_value = None
        aggregator = OddsAggregator()
        
        # Should still have offshore scraper
        assert 'offshore_scraper' in aggregator.providers
        # Should not have the_odds_api without key
        assert 'the_odds_api' not in aggregator.providers
    
    def test_arbitrage_detection_logic(self):
        """Test arbitrage opportunity detection logic"""
        aggregator = OddsAggregator()
        
        # Mock game data with arbitrage opportunity
        game_data = {
            'id': 'test_game',
            'home_team': 'Team A',
            'away_team': 'Team B',
            'commence_time': '2024-07-15T19:00:00Z',
            'bookmakers': [
                {
                    'key': 'bookmaker1',
                    'markets': [{
                        'key': 'h2h',
                        'last_update': '2024-07-15T18:00:00Z',
                        'outcomes': [
                            {'name': 'Team A', 'price': +150},  # Implied prob: 0.4
                            {'name': 'Team B', 'price': +200}   # Implied prob: 0.333
                        ]
                    }]
                }
            ]
        }
        
        # Total implied probability: 0.4 + 0.333 = 0.733
        # Profit margin: 1 - 0.733 = 0.267 (26.7%)
        arb_opp = aggregator._find_market_arbitrage(game_data, 'h2h', 0.01)
        
        assert arb_opp is not None
        assert arb_opp['profit_margin'] > 0.2  # Should be around 26.7%
        assert arb_opp['market_type'] == 'h2h'
        assert 'Team A' in arb_opp['best_odds']
        assert 'Team B' in arb_opp['best_odds']


class TestOddsAPIEndpoints:
    """Test the FastAPI endpoints for odds"""
    
    def test_health_endpoint(self):
        """Test the odds API health endpoint"""
        response = client.get("/api/v1/odds/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "odds_api"
        assert "timestamp" in data
    
    @patch('app.api.odds.get_provider_status')
    def test_providers_status_endpoint(self, mock_status):
        """Test the providers status endpoint"""
        mock_status.return_value = {
            'timestamp': '2024-07-15T18:00:00Z',
            'providers': {
                'offshore_scraper': {'status': 'available', 'type': 'scraper'}
            }
        }
        
        response = client.get("/api/v1/odds/providers/status")
        assert response.status_code == 200
        data = response.json()
        assert 'providers' in data
        assert 'timestamp' in data
    
    @patch('app.api.odds.get_wnba_odds')
    def test_get_odds_endpoint_success(self, mock_get_odds):
        """Test successful odds retrieval endpoint"""
        mock_get_odds.return_value = {
            'aggregated_at': '2024-07-15T18:00:00Z',
            'sources': {
                'the_odds_api': {
                    'total_games': 1,
                    'data': [{
                        'id': 'test_game',
                        'home_team': 'Team A',
                        'away_team': 'Team B',
                        'bookmakers': []
                    }]
                }
            },
            'summary': {
                'total_sources': 1,
                'successful_sources': 1,
                'total_games': 1,
                'total_bookmakers': []
            }
        }
        
        response = client.get("/api/v1/odds/")
        assert response.status_code == 200
        data = response.json()
        assert 'sources' in data
        assert 'summary' in data
    
    @patch('app.api.odds.find_arbitrage_opportunities')
    def test_arbitrage_endpoint_success(self, mock_find_arb):
        """Test arbitrage opportunities endpoint"""
        mock_find_arb.return_value = [
            {
                'game_id': 'test_game',
                'game': 'Team A @ Team B',
                'market_type': 'h2h',
                'profit_margin': 0.05,
                'profit_percentage': 5.0,
                'best_odds': {},
                'detected_at': '2024-07-15T18:00:00Z'
            }
        ]
        
        response = client.get("/api/v1/odds/arbitrage?min_profit=0.01")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['profit_percentage'] == 5.0
    
    @patch('app.api.odds.find_arbitrage_opportunities')
    def test_arbitrage_summary_endpoint(self, mock_find_arb):
        """Test arbitrage summary endpoint"""
        mock_find_arb.return_value = [
            {
                'profit_percentage': 3.5,
                'market_type': 'h2h',
                'best_odds': {
                    'Team A': {'bookmaker': 'book1'},
                    'Team B': {'bookmaker': 'book2'}
                }
            },
            {
                'profit_percentage': 2.1,
                'market_type': 'spreads',
                'best_odds': {
                    'Team C +5.5': {'bookmaker': 'book1'},
                    'Team D -5.5': {'bookmaker': 'book3'}
                }
            }
        ]
        
        response = client.get("/api/v1/odds/arbitrage/summary")
        assert response.status_code == 200
        data = response.json()
        
        assert data['total_opportunities'] == 2
        assert data['average_profit'] == (3.5 + 2.1) / 2
        assert data['best_profit'] == 3.5
        assert 'h2h' in data['markets_summary']
        assert 'spreads' in data['markets_summary']
    
    @patch('app.api.odds.get_wnba_odds')
    def test_odds_endpoint_api_error(self, mock_get_odds):
        """Test odds endpoint when API error occurs"""
        mock_get_odds.side_effect = OddsAPIError("API rate limit exceeded")
        
        response = client.get("/api/v1/odds/")
        assert response.status_code == 503
        assert "Odds service error" in response.json()["detail"]


# Integration test functions
def test_can_import_all_modules():
    """Test that all odds-related modules can be imported"""
    from app.services.odds_api import (
        TheOddsAPI, 
        OddsAggregator, 
        OffshoreBookScraper,
        get_wnba_odds,
        find_arbitrage_opportunities,
        get_provider_status
    )
    from app.api.odds import router
    
    # All imports successful
    assert True


@pytest.mark.integration
def test_service_without_api_key():
    """Integration test - service should work without API key but with limited functionality"""
    with patch.dict(os.environ, {}, clear=True):
        # Should not crash
        status = get_provider_status()
        assert 'providers' in status
        
        # Should handle missing API key gracefully
        odds_data = get_wnba_odds()
        assert 'errors' in odds_data or 'sources' in odds_data


if __name__ == "__main__":
    # Run basic smoke tests
    print("Running basic odds API smoke tests...")
    
    # Test imports
    test_can_import_all_modules()
    print("✅ All modules import successfully")
    
    # Test service without API key
    test_service_without_api_key()
    print("✅ Service handles missing API key gracefully")
    
    print("🎉 All smoke tests passed!") 