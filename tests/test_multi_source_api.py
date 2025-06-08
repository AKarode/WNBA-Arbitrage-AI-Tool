"""
Tests for Multi-Source Odds API Endpoints
Comprehensive test suite for the enhanced API endpoints
"""

import pytest
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.services.multi_source_ingestion import OddsData, ArbitrageOpportunity
from app.config.data_sources import get_enabled_sources

# Test client
client = TestClient(app)

# Test fixtures
@pytest.fixture
def sample_odds_data():
    """Sample odds data for testing"""
    return [
        OddsData(
            game_id="test_game_1",
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
            game_id="test_game_1",
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
        )
    ]

@pytest.fixture
def sample_arbitrage_opportunity():
    """Sample arbitrage opportunity for testing"""
    return ArbitrageOpportunity(
        game_id="test_game_1",
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
def mock_redis():
    """Mock Redis client for testing"""
    with patch('app.services.multi_source_ingestion.redis.Redis') as mock:
        redis_instance = Mock()
        redis_instance.get.return_value = None
        redis_instance.setex.return_value = True
        redis_instance.incr.return_value = 1
        redis_instance.expire.return_value = True
        redis_instance.pipeline.return_value = redis_instance
        redis_instance.execute.return_value = [1, True, 1, True]
        redis_instance.ping.return_value = True
        mock.return_value = redis_instance
        yield redis_instance

class TestMultiSourceOddsEndpoints:
    """Test suite for multi-source odds API endpoints"""

    @patch('app.api.multi_source_odds.get_multi_source_odds')
    def test_get_multi_source_current_odds_success(self, mock_get_odds, sample_odds_data, mock_redis):
        """Test successful retrieval of multi-source odds"""
        # Mock the response
        mock_get_odds.return_value = {
            'bovada_scraper': sample_odds_data[:1],
            'betonline_scraper': sample_odds_data[1:]
        }
        
        response = client.get("/api/v2/odds/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'aggregated_at' in data
        assert 'sources' in data
        assert 'summary' in data
        assert 'enabled_sources' in data
        assert 'data_freshness' in data
        
        # Check sources data
        assert 'bovada_scraper' in data['sources']
        assert 'betonline_scraper' in data['sources']
        
        # Check summary
        assert data['summary']['total_odds_entries'] >= 0
        assert 'sources_with_data' in data['summary']

    @patch('app.api.multi_source_odds.get_multi_source_odds')
    def test_get_multi_source_odds_with_filters(self, mock_get_odds, sample_odds_data, mock_redis):
        """Test odds retrieval with various filters"""
        mock_get_odds.return_value = {
            'bovada_scraper': sample_odds_data[:1],
            'betonline_scraper': sample_odds_data[1:]
        }
        
        # Test with source filter
        response = client.get("/api/v2/odds/?sources=bovada_scraper")
        assert response.status_code == 200
        
        # Test with bookmaker filter
        response = client.get("/api/v2/odds/?bookmakers=bovada,betonline")
        assert response.status_code == 200
        
        # Test with market filter
        response = client.get("/api/v2/odds/?markets=h2h,spreads")
        assert response.status_code == 200
        
        # Test with fresh_only filter
        response = client.get("/api/v2/odds/?fresh_only=true")
        assert response.status_code == 200

    @patch('app.api.multi_source_odds.get_multi_source_odds')
    def test_get_multi_source_odds_error_handling(self, mock_get_odds, mock_redis):
        """Test error handling for odds retrieval"""
        # Mock an exception
        mock_get_odds.side_effect = Exception("Data source unavailable")
        
        response = client.get("/api/v2/odds/")
        
        assert response.status_code == 500
        assert "Failed to fetch multi-source odds" in response.json()['detail']

class TestArbitrageEndpoints:
    """Test suite for arbitrage detection endpoints"""

    @patch('app.api.multi_source_odds.find_real_time_arbitrage')
    def test_get_real_time_arbitrage_success(self, mock_find_arbitrage, sample_arbitrage_opportunity, mock_redis):
        """Test successful real-time arbitrage detection"""
        mock_find_arbitrage.return_value = [sample_arbitrage_opportunity]
        
        response = client.get("/api/v2/odds/arbitrage/real-time")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 1
        
        opportunity = data[0]
        assert opportunity['game_id'] == 'test_game_1'
        assert opportunity['profit_percentage'] == 2.5
        assert 'best_odds' in opportunity
        assert 'execution_plan' in opportunity
        assert 'risk_assessment' in opportunity

    @patch('app.api.multi_source_odds.find_real_time_arbitrage')
    def test_get_real_time_arbitrage_with_filters(self, mock_find_arbitrage, sample_arbitrage_opportunity, mock_redis):
        """Test arbitrage detection with various filters"""
        mock_find_arbitrage.return_value = [sample_arbitrage_opportunity]
        
        # Test with min_profit filter
        response = client.get("/api/v2/odds/arbitrage/real-time?min_profit=0.03")
        assert response.status_code == 200
        
        # Test with max_opportunities filter
        response = client.get("/api/v2/odds/arbitrage/real-time?max_opportunities=5")
        assert response.status_code == 200
        
        # Test with sources filter
        response = client.get("/api/v2/odds/arbitrage/real-time?sources=bovada_scraper,betonline_scraper")
        assert response.status_code == 200
        
        # Test with markets filter
        response = client.get("/api/v2/odds/arbitrage/real-time?markets=h2h")
        assert response.status_code == 200

    def test_get_real_time_arbitrage_invalid_profit_margin(self, mock_redis):
        """Test arbitrage detection with invalid profit margin"""
        # Test profit margin too low
        response = client.get("/api/v2/odds/arbitrage/real-time?min_profit=0.0001")
        assert response.status_code == 400
        assert "Invalid profit margin" in response.json()['detail']
        
        # Test profit margin too high
        response = client.get("/api/v2/odds/arbitrage/real-time?min_profit=0.8")
        assert response.status_code == 400
        assert "Invalid profit margin" in response.json()['detail']

    @patch('app.api.multi_source_odds.find_real_time_arbitrage')
    def test_get_arbitrage_market_summary(self, mock_find_arbitrage, sample_arbitrage_opportunity, mock_redis):
        """Test arbitrage market summary endpoint"""
        mock_find_arbitrage.return_value = [sample_arbitrage_opportunity]
        
        response = client.get("/api/v2/odds/arbitrage/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'analysis_timestamp' in data
        assert 'current_opportunities' in data
        assert 'market_efficiency' in data
        assert 'source_performance' in data
        assert 'recommendations' in data
        assert 'alert_thresholds' in data
        
        # Check current_opportunities structure
        current_opps = data['current_opportunities']
        assert 'total_count' in current_opps
        assert 'by_market' in current_opps
        assert 'by_profit_range' in current_opps
        assert 'average_profit' in current_opps

    @patch('app.api.multi_source_odds.find_real_time_arbitrage')
    def test_get_arbitrage_summary_no_opportunities(self, mock_find_arbitrage, mock_redis):
        """Test arbitrage summary when no opportunities exist"""
        mock_find_arbitrage.return_value = []
        
        response = client.get("/api/v2/odds/arbitrage/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['current_opportunities']['total_count'] == 0
        assert data['current_opportunities']['average_profit'] == 0
        assert data['current_opportunities']['best_opportunity'] is None

class TestSourceManagementEndpoints:
    """Test suite for source management endpoints"""

    @patch('app.api.multi_source_odds.get_source_health')
    def test_get_all_sources_status(self, mock_get_health, mock_redis):
        """Test retrieval of all sources status"""
        mock_get_health.return_value = {
            'timestamp': datetime.utcnow().isoformat(),
            'sources': {
                'odds_api': {
                    'status': 'healthy',
                    'rate_limit_status': 'ok'
                },
                'bovada_scraper': {
                    'status': 'operational',
                    'rate_limit_status': 'ok'
                }
            }
        }
        
        response = client.get("/api/v2/odds/sources/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'timestamp' in data
        assert 'sources' in data
        
        # Check that performance metrics are added
        for source_name, source_data in data['sources'].items():
            assert 'performance_metrics' in source_data
            assert 'recent_errors' in source_data
            assert 'data_quality_score' in source_data

    @patch('app.api.multi_source_odds.get_multi_source_odds')
    def test_get_single_source_odds_valid_source(self, mock_get_odds, sample_odds_data, mock_redis):
        """Test retrieval of odds from a single valid source"""
        mock_get_odds.return_value = {
            'bovada_scraper': sample_odds_data[:1],
            'betonline_scraper': sample_odds_data[1:]
        }
        
        with patch('app.api.multi_source_odds.get_enabled_sources', return_value=['bovada_scraper', 'betonline_scraper']):
            response = client.get("/api/v2/odds/sources/bovada_scraper/odds")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if data:  # If data exists
            assert data[0]['source'] == 'bovada_scraper'
            assert 'game_id' in data[0]
            assert 'bookmaker' in data[0]

    def test_get_single_source_odds_invalid_source(self, mock_redis):
        """Test retrieval from invalid/disabled source"""
        with patch('app.api.multi_source_odds.get_enabled_sources', return_value=['bovada_scraper']):
            response = client.get("/api/v2/odds/sources/invalid_source/odds")
        
        assert response.status_code == 404
        assert "not found or disabled" in response.json()['detail']

    @patch('app.api.multi_source_odds.get_multi_source_odds')
    def test_get_single_source_odds_with_market_filter(self, mock_get_odds, sample_odds_data, mock_redis):
        """Test single source odds with market filtering"""
        mock_get_odds.return_value = {
            'bovada_scraper': sample_odds_data[:1]
        }
        
        with patch('app.api.multi_source_odds.get_enabled_sources', return_value=['bovada_scraper']):
            response = client.get("/api/v2/odds/sources/bovada_scraper/odds?markets=h2h")
        
        assert response.status_code == 200

class TestSimulationEndpoints:
    """Test suite for arbitrage simulation endpoints"""

    def test_simulate_arbitrage_execution_valid_data(self, mock_redis):
        """Test arbitrage execution simulation with valid data"""
        opportunity_data = {
            'game_id': 'test_game_1',
            'market_type': 'h2h',
            'best_odds': {
                'Team A': {'price': -130, 'bookmaker': 'bovada'},
                'Team B': {'price': 120, 'bookmaker': 'betonline'}
            }
        }
        
        response = client.post(
            "/api/v2/odds/arbitrage/simulate?total_stake=1000",
            json=opportunity_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'simulation_timestamp' in data
        assert 'input_parameters' in data
        assert 'profit_projection' in data
        assert 'execution_plan' in data
        assert 'risk_analysis' in data
        assert 'timing_recommendations' in data
        assert 'success_probability' in data
        
        # Check profit projection structure
        profit_proj = data['profit_projection']
        assert 'gross_profit' in profit_proj
        assert 'fees' in profit_proj
        assert 'net_profit' in profit_proj
        assert 'roi_percentage' in profit_proj

    def test_simulate_arbitrage_execution_invalid_data(self, mock_redis):
        """Test simulation with invalid opportunity data"""
        invalid_data = {
            'invalid_field': 'invalid_value'
        }
        
        response = client.post(
            "/api/v2/odds/arbitrage/simulate",
            json=invalid_data
        )
        
        assert response.status_code == 400
        assert "Invalid opportunity data" in response.json()['detail']

    def test_simulate_arbitrage_execution_with_parameters(self, mock_redis):
        """Test simulation with various parameters"""
        opportunity_data = {
            'game_id': 'test_game_1',
            'market_type': 'h2h',
            'best_odds': {
                'Team A': {'price': -130, 'bookmaker': 'bovada'},
                'Team B': {'price': 120, 'bookmaker': 'betonline'}
            }
        }
        
        # Test with different parameters
        response = client.post(
            "/api/v2/odds/arbitrage/simulate?total_stake=2000&include_fees=true&risk_tolerance=high",
            json=opportunity_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['input_parameters']['total_stake'] == 2000
        assert data['input_parameters']['include_fees'] == True
        assert data['input_parameters']['risk_tolerance'] == 'high'

class TestHealthEndpoints:
    """Test suite for health check endpoints"""

    @patch('app.api.multi_source_odds.get_source_health')
    def test_health_check_multi_source_healthy(self, mock_get_health, mock_redis):
        """Test health check when all sources are healthy"""
        mock_get_health.return_value = {
            'sources': {
                'odds_api': {'status': 'healthy'},
                'bovada_scraper': {'status': 'healthy'},
                'betonline_scraper': {'status': 'healthy'}
            }
        }
        
        response = client.get("/api/v2/odds/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['overall_status'] == 'healthy'
        assert 'timestamp' in data
        assert 'sources' in data
        assert 'system_metrics' in data
        assert 'performance_indicators' in data
        assert data['version'] == '2.0.0'
        
        # Check system metrics
        metrics = data['system_metrics']
        assert 'enabled_sources' in metrics
        assert 'total_sources' in metrics
        assert 'healthy_sources' in metrics

    @patch('app.api.multi_source_odds.get_source_health')
    def test_health_check_multi_source_degraded(self, mock_get_health, mock_redis):
        """Test health check when some sources are unhealthy"""
        mock_get_health.return_value = {
            'sources': {
                'odds_api': {'status': 'healthy'},
                'bovada_scraper': {'status': 'error'},
                'betonline_scraper': {'status': 'healthy'}
            }
        }
        
        response = client.get("/api/v2/odds/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be degraded since not all sources are healthy
        assert data['overall_status'] in ['degraded', 'partial']

    @patch('app.api.multi_source_odds.get_source_health')
    def test_health_check_multi_source_critical(self, mock_get_health, mock_redis):
        """Test health check when no sources are healthy"""
        mock_get_health.return_value = {
            'sources': {
                'odds_api': {'status': 'error'},
                'bovada_scraper': {'status': 'error'},
                'betonline_scraper': {'status': 'error'}
            }
        }
        
        response = client.get("/api/v2/odds/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['overall_status'] == 'critical'

    @patch('app.api.multi_source_odds.get_source_health')
    def test_health_check_exception_handling(self, mock_get_health, mock_redis):
        """Test health check exception handling"""
        mock_get_health.side_effect = Exception("Health check failed")
        
        response = client.get("/api/v2/odds/health")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data['overall_status'] == 'error'
        assert 'error' in data
        assert data['version'] == '2.0.0'

class TestParameterValidation:
    """Test suite for parameter validation"""

    def test_profit_margin_validation(self, mock_redis):
        """Test profit margin parameter validation"""
        # Test minimum bound
        response = client.get("/api/v2/odds/arbitrage/real-time?min_profit=0.004")
        assert response.status_code == 422  # Validation error
        
        # Test maximum bound
        response = client.get("/api/v2/odds/arbitrage/real-time?min_profit=0.6")
        assert response.status_code == 422  # Validation error
        
        # Test valid range
        with patch('app.api.multi_source_odds.find_real_time_arbitrage', return_value=[]):
            response = client.get("/api/v2/odds/arbitrage/real-time?min_profit=0.02")
            assert response.status_code == 200

    def test_max_opportunities_validation(self, mock_redis):
        """Test max_opportunities parameter validation"""
        # Test minimum bound
        response = client.get("/api/v2/odds/arbitrage/real-time?max_opportunities=0")
        assert response.status_code == 422
        
        # Test maximum bound
        response = client.get("/api/v2/odds/arbitrage/real-time?max_opportunities=101")
        assert response.status_code == 422
        
        # Test valid range
        with patch('app.api.multi_source_odds.find_real_time_arbitrage', return_value=[]):
            response = client.get("/api/v2/odds/arbitrage/real-time?max_opportunities=50")
            assert response.status_code == 200

    def test_stake_validation(self, mock_redis):
        """Test stake parameter validation"""
        opportunity_data = {
            'game_id': 'test_game_1',
            'market_type': 'h2h',
            'best_odds': {'Team A': {'price': -130}, 'Team B': {'price': 120}}
        }
        
        # Test minimum bound
        response = client.post(
            "/api/v2/odds/arbitrage/simulate?total_stake=50",
            json=opportunity_data
        )
        assert response.status_code == 422
        
        # Test maximum bound
        response = client.post(
            "/api/v2/odds/arbitrage/simulate?total_stake=200000",
            json=opportunity_data
        )
        assert response.status_code == 422

class TestRateLimitingIntegration:
    """Test suite for rate limiting integration"""

    @patch('app.services.multi_source_ingestion.RateLimitManager')
    def test_rate_limiting_respected(self, mock_rate_limiter, mock_redis):
        """Test that rate limiting is properly respected"""
        # Mock rate limiter to deny requests
        rate_limiter_instance = Mock()
        rate_limiter_instance.can_make_request.return_value = False
        mock_rate_limiter.return_value = rate_limiter_instance
        
        with patch('app.api.multi_source_odds.get_multi_source_odds', return_value={}):
            response = client.get("/api/v2/odds/")
            
        assert response.status_code == 200  # Should still return, but with limited data

    @patch('app.services.multi_source_ingestion.RateLimitManager')
    def test_rate_limiting_requests_recorded(self, mock_rate_limiter, mock_redis):
        """Test that requests are properly recorded for rate limiting"""
        rate_limiter_instance = Mock()
        rate_limiter_instance.can_make_request.return_value = True
        rate_limiter_instance.record_request.return_value = None
        mock_rate_limiter.return_value = rate_limiter_instance
        
        with patch('app.api.multi_source_odds.get_multi_source_odds', return_value={}):
            response = client.get("/api/v2/odds/")
            
        assert response.status_code == 200

class TestErrorHandling:
    """Test suite for comprehensive error handling"""

    @patch('app.api.multi_source_odds.get_multi_source_odds')
    def test_timeout_error_handling(self, mock_get_odds, mock_redis):
        """Test handling of timeout errors"""
        import asyncio
        mock_get_odds.side_effect = asyncio.TimeoutError("Request timeout")
        
        response = client.get("/api/v2/odds/")
        
        assert response.status_code == 500
        assert "Failed to fetch multi-source odds" in response.json()['detail']

    @patch('app.api.multi_source_odds.find_real_time_arbitrage')
    def test_connection_error_handling(self, mock_find_arbitrage, mock_redis):
        """Test handling of connection errors"""
        import aiohttp
        mock_find_arbitrage.side_effect = aiohttp.ClientError("Connection failed")
        
        response = client.get("/api/v2/odds/arbitrage/real-time")
        
        assert response.status_code == 500
        assert "Failed to find arbitrage opportunities" in response.json()['detail']

    def test_malformed_json_handling(self, mock_redis):
        """Test handling of malformed JSON in request body"""
        response = client.post(
            "/api/v2/odds/arbitrage/simulate",
            data="invalid json data",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity

class TestDataIntegrity:
    """Test suite for data integrity checks"""

    @patch('app.api.multi_source_odds.get_multi_source_odds')
    def test_odds_data_structure_validation(self, mock_get_odds, mock_redis):
        """Test validation of odds data structure"""
        # Mock malformed odds data
        malformed_data = {
            'source1': [{'invalid': 'structure'}],
            'source2': []
        }
        mock_get_odds.return_value = malformed_data
        
        response = client.get("/api/v2/odds/")
        
        # Should handle malformed data gracefully
        assert response.status_code == 200
        data = response.json()
        assert 'sources' in data

    @patch('app.api.multi_source_odds.find_real_time_arbitrage')
    def test_arbitrage_opportunity_validation(self, mock_find_arbitrage, mock_redis):
        """Test validation of arbitrage opportunity data"""
        # Mock arbitrage opportunity with missing fields
        incomplete_opportunity = Mock()
        incomplete_opportunity.game_id = "test"
        incomplete_opportunity.profit_percentage = 2.5
        # Missing other required fields
        
        mock_find_arbitrage.return_value = [incomplete_opportunity]
        
        response = client.get("/api/v2/odds/arbitrage/real-time")
        
        # Should handle incomplete data gracefully
        assert response.status_code == 200

# Performance tests
class TestPerformance:
    """Test suite for performance requirements"""

    @patch('app.api.multi_source_odds.get_multi_source_odds')
    def test_response_time_requirements(self, mock_get_odds, mock_redis):
        """Test that responses meet time requirements"""
        import time
        
        mock_get_odds.return_value = {}
        
        start_time = time.time()
        response = client.get("/api/v2/odds/")
        end_time = time.time()
        
        assert response.status_code == 200
        # Response should be under 2 seconds (generous for testing)
        assert (end_time - start_time) < 2.0

    @patch('app.api.multi_source_odds.find_real_time_arbitrage')
    def test_large_dataset_handling(self, mock_find_arbitrage, sample_arbitrage_opportunity, mock_redis):
        """Test handling of large datasets"""
        # Create a large list of opportunities
        large_opportunity_list = [sample_arbitrage_opportunity] * 100
        mock_find_arbitrage.return_value = large_opportunity_list
        
        response = client.get("/api/v2/odds/arbitrage/real-time?max_opportunities=50")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should respect the max_opportunities limit
        assert len(data) <= 50

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])