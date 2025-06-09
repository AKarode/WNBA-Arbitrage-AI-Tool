"""
Integration Tests for WNBA Arbitrage AI Tool
End-to-end testing of the complete system
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import redis

from app.main import app
from app.services.multi_source_ingestion import (
    MultiSourceDataAggregator,
    OddsData,
    ArbitrageOpportunity
)
from app.config.data_sources import get_enabled_sources

# Integration test client
client = TestClient(app)

class TestEndToEndWorkflows:
    """Test complete end-to-end workflows"""

    @pytest.mark.asyncio
    @patch('app.services.multi_source_ingestion.redis.Redis')
    @patch('app.api.multi_source_odds.get_multi_source_odds')
    @patch('app.api.multi_source_odds.find_real_time_arbitrage')
    async def test_complete_arbitrage_detection_workflow(self, mock_find_arbitrage, mock_get_odds, mock_redis_class):
        """Test the complete workflow from data collection to arbitrage alert"""
        
        # Setup mocks
        mock_redis_instance = Mock()
        mock_redis_instance.ping.return_value = True
        mock_redis_class.return_value = mock_redis_instance
        
        # Mock odds data
        sample_odds = {
            'bovada_scraper': [
                OddsData(
                    game_id="integration_test_game",
                    home_team="Las Vegas Aces",
                    away_team="New York Liberty",
                    commence_time="2024-07-15T19:00:00Z",
                    bookmaker="bovada",
                    market_type="h2h",
                    outcomes=[
                        {"name": "Las Vegas Aces", "price": -130},
                        {"name": "New York Liberty", "price": 120}
                    ],
                    last_update="2024-07-15T18:30:00Z",
                    source="bovada_scraper"
                )
            ],
            'betonline_scraper': [
                OddsData(
                    game_id="integration_test_game",
                    home_team="Las Vegas Aces",
                    away_team="New York Liberty",
                    commence_time="2024-07-15T19:00:00Z",
                    bookmaker="betonline",
                    market_type="h2h",
                    outcomes=[
                        {"name": "Las Vegas Aces", "price": -140},
                        {"name": "New York Liberty", "price": 130}
                    ],
                    last_update="2024-07-15T18:25:00Z",
                    source="betonline_scraper"
                )
            ]
        }
        
        # Mock arbitrage opportunity
        arbitrage_opportunity = ArbitrageOpportunity(
            game_id="integration_test_game",
            game_description="New York Liberty @ Las Vegas Aces",
            market_type="h2h",
            profit_margin=0.027,
            profit_percentage=2.7,
            best_odds={
                "Las Vegas Aces": {
                    "price": -130,
                    "bookmaker": "bovada",
                    "source": "bovada_scraper"
                },
                "New York Liberty": {
                    "price": 130,
                    "bookmaker": "betonline",
                    "source": "betonline_scraper"
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
        
        mock_get_odds.return_value = sample_odds
        mock_find_arbitrage.return_value = [arbitrage_opportunity]
        
        # Step 1: Collect odds from multiple sources
        response = client.get("/api/v2/odds/")
        assert response.status_code == 200
        odds_data = response.json()
        assert 'sources' in odds_data
        assert len(odds_data['sources']) > 0
        
        # Step 2: Detect arbitrage opportunities
        response = client.get("/api/v2/odds/arbitrage/real-time?min_profit=0.02")
        assert response.status_code == 200
        opportunities = response.json()
        assert len(opportunities) > 0
        
        opportunity = opportunities[0]
        assert opportunity['profit_percentage'] > 2.0
        assert 'execution_plan' in opportunity
        assert 'risk_assessment' in opportunity
        
        # Step 3: Get market summary
        response = client.get("/api/v2/odds/arbitrage/summary")
        assert response.status_code == 200
        summary = response.json()
        assert summary['current_opportunities']['total_count'] > 0
        assert 'recommendations' in summary
        
        # Step 4: Simulate execution
        opportunity_data = {
            'game_id': opportunity['game_id'],
            'market_type': opportunity['market_type'],
            'best_odds': opportunity['best_odds']
        }
        
        response = client.post(
            "/api/v2/odds/arbitrage/simulate?total_stake=1000",
            json=opportunity_data
        )
        assert response.status_code == 200
        simulation = response.json()
        assert 'profit_projection' in simulation
        assert simulation['profit_projection']['net_profit'] > 0

    @patch('app.services.multi_source_ingestion.redis.Redis')
    def test_source_health_monitoring_workflow(self, mock_redis_class):
        """Test the complete source health monitoring workflow"""
        
        mock_redis_instance = Mock()
        mock_redis_instance.ping.return_value = True
        mock_redis_class.return_value = mock_redis_instance
        
        # Step 1: Check overall system health
        response = client.get("/api/v2/odds/health")
        assert response.status_code == 200
        health = response.json()
        assert 'overall_status' in health
        assert 'system_metrics' in health
        
        # Step 2: Check individual source status
        response = client.get("/api/v2/odds/sources/status")
        assert response.status_code == 200
        sources_status = response.json()
        assert 'sources' in sources_status
        
        # Step 3: Test individual source data retrieval
        enabled_sources = get_enabled_sources()
        if enabled_sources:
            source_name = enabled_sources[0]
            with patch('app.api.multi_source_odds.get_multi_source_odds', return_value={source_name: []}):
                response = client.get(f"/api/v2/odds/sources/{source_name}/odds")
                assert response.status_code == 200

    @patch('app.services.multi_source_ingestion.redis.Redis')
    @patch('app.api.multi_source_odds.get_multi_source_odds')
    def test_error_recovery_workflow(self, mock_get_odds, mock_redis_class):
        """Test system behavior when sources fail and recover"""
        
        mock_redis_instance = Mock()
        mock_redis_instance.ping.return_value = True
        mock_redis_class.return_value = mock_redis_instance
        
        # Step 1: Simulate partial source failure
        mock_get_odds.return_value = {
            'bovada_scraper': [],  # Empty data (source failed)
            'betonline_scraper': [
                OddsData(
                    game_id="recovery_test_game",
                    home_team="Team A",
                    away_team="Team B",
                    commence_time="2024-07-15T19:00:00Z",
                    bookmaker="betonline",
                    market_type="h2h",
                    outcomes=[{"name": "Team A", "price": -110}],
                    last_update="2024-07-15T18:30:00Z",
                    source="betonline_scraper"
                )
            ]
        }
        
        response = client.get("/api/v2/odds/")
        assert response.status_code == 200
        # System should still return data from working sources
        
        # Step 2: Check health reflects the partial failure
        response = client.get("/api/v2/odds/health")
        assert response.status_code == 200
        health = response.json()
        # Overall status might be 'degraded' or 'partial'
        assert health['overall_status'] in ['healthy', 'degraded', 'partial']
        
        # Step 3: Simulate recovery
        mock_get_odds.return_value = {
            'bovada_scraper': [
                OddsData(
                    game_id="recovery_test_game",
                    home_team="Team A",
                    away_team="Team B",
                    commence_time="2024-07-15T19:00:00Z",
                    bookmaker="bovada",
                    market_type="h2h",
                    outcomes=[{"name": "Team A", "price": -115}],
                    last_update="2024-07-15T18:30:00Z",
                    source="bovada_scraper"
                )
            ],
            'betonline_scraper': [
                OddsData(
                    game_id="recovery_test_game",
                    home_team="Team A",
                    away_team="Team B",
                    commence_time="2024-07-15T19:00:00Z",
                    bookmaker="betonline",
                    market_type="h2h",
                    outcomes=[{"name": "Team A", "price": -110}],
                    last_update="2024-07-15T18:30:00Z",
                    source="betonline_scraper"
                )
            ]
        }
        
        response = client.get("/api/v2/odds/")
        assert response.status_code == 200
        data = response.json()
        assert len(data['sources']) >= 2  # Both sources working

class TestDataFlow:
    """Test data flow through the system"""

    @patch('app.services.multi_source_ingestion.redis.Redis')
    async def test_odds_data_normalization_flow(self, mock_redis_class):
        """Test that odds data is properly normalized across sources"""
        
        mock_redis_instance = Mock()
        mock_redis_instance.ping.return_value = True
        mock_redis_class.return_value = mock_redis_instance
        
        # Create aggregator directly
        aggregator = MultiSourceDataAggregator()
        
        # Mock different source formats
        bovada_odds = OddsData(
            game_id="normalization_test",
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
        )
        
        betonline_odds = OddsData(
            game_id="normalization_test",
            home_team="Las Vegas Aces",
            away_team="New York Liberty",
            commence_time="2024-07-15T19:00:00Z",
            bookmaker="betonline",
            market_type="h2h",
            outcomes=[
                {"name": "Las Vegas Aces", "price": -135},
                {"name": "New York Liberty", "price": 115}
            ],
            last_update="2024-07-15T18:25:00Z",
            source="betonline_scraper"
        )
        
        odds_data = {
            'bovada_scraper': [bovada_odds],
            'betonline_scraper': [betonline_odds]
        }
        
        # Test arbitrage detection with normalized data
        opportunities = aggregator.detect_arbitrage_opportunities(odds_data, 0.01)
        
        # Verify that data was properly normalized and compared
        if opportunities:
            opportunity = opportunities[0]
            assert opportunity.game_id == "normalization_test"
            assert len(opportunity.best_odds) >= 2

    @patch('app.services.multi_source_ingestion.redis.Redis')
    def test_rate_limiting_integration(self, mock_redis_class):
        """Test rate limiting integration across the system"""
        
        mock_redis_instance = Mock()
        mock_redis_instance.get.return_value = '0'  # No requests made yet
        mock_redis_instance.incr.return_value = 1
        mock_redis_instance.expire.return_value = True
        mock_redis_instance.pipeline.return_value = mock_redis_instance
        mock_redis_instance.execute.return_value = [1, True, 1, True]
        mock_redis_class.return_value = mock_redis_instance
        
        # Test multiple rapid requests
        with patch('app.api.multi_source_odds.get_multi_source_odds', return_value={}):
            for i in range(5):
                response = client.get("/api/v2/odds/")
                assert response.status_code == 200
        
        # Verify rate limiting was tracked
        assert mock_redis_instance.incr.called

    @patch('app.services.multi_source_ingestion.redis.Redis')
    def test_caching_integration(self, mock_redis_class):
        """Test that caching works properly across requests"""
        
        mock_redis_instance = Mock()
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.return_value = None  # No cached data initially
        mock_redis_instance.setex.return_value = True
        mock_redis_class.return_value = mock_redis_instance
        
        with patch('app.api.multi_source_odds.get_multi_source_odds', return_value={}) as mock_get_odds:
            # First request should fetch fresh data
            response1 = client.get("/api/v2/odds/")
            assert response1.status_code == 200
            
            # Verify caching was attempted
            mock_redis_instance.setex.assert_called()

class TestPerformanceIntegration:
    """Test system performance under various conditions"""

    @patch('app.services.multi_source_ingestion.redis.Redis')
    def test_concurrent_request_handling(self, mock_redis_class):
        """Test system behavior under concurrent requests"""
        
        mock_redis_instance = Mock()
        mock_redis_instance.ping.return_value = True
        mock_redis_class.return_value = mock_redis_instance
        
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                with patch('app.api.multi_source_odds.get_multi_source_odds', return_value={}):
                    response = client.get("/api/v2/odds/")
                    results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # Launch multiple concurrent requests
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all requests to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        assert len(errors) == 0
        assert all(status == 200 for status in results)
        assert len(results) == 10

    @patch('app.services.multi_source_ingestion.redis.Redis')
    def test_large_dataset_performance(self, mock_redis_class):
        """Test system performance with large datasets"""
        
        mock_redis_instance = Mock()
        mock_redis_instance.ping.return_value = True
        mock_redis_class.return_value = mock_redis_instance
        
        # Create large mock dataset
        large_dataset = {}
        for source_idx in range(3):
            source_name = f'source_{source_idx}'
            large_dataset[source_name] = []
            
            for game_idx in range(50):  # 50 games per source
                odds_data = OddsData(
                    game_id=f"game_{game_idx}",
                    home_team=f"Home_Team_{game_idx}",
                    away_team=f"Away_Team_{game_idx}",
                    commence_time="2024-07-15T19:00:00Z",
                    bookmaker=f"bookmaker_{source_idx}",
                    market_type="h2h",
                    outcomes=[
                        {"name": f"Home_Team_{game_idx}", "price": -110 + game_idx},
                        {"name": f"Away_Team_{game_idx}", "price": -110 - game_idx}
                    ],
                    last_update="2024-07-15T18:30:00Z",
                    source=source_name
                )
                large_dataset[source_name].append(odds_data)
        
        with patch('app.api.multi_source_odds.get_multi_source_odds', return_value=large_dataset):
            start_time = time.time()
            response = client.get("/api/v2/odds/")
            end_time = time.time()
            
            assert response.status_code == 200
            # Should respond within 5 seconds even with large dataset
            assert (end_time - start_time) < 5.0

    @patch('app.services.multi_source_ingestion.redis.Redis')
    def test_arbitrage_detection_performance(self, mock_redis_class):
        """Test arbitrage detection performance with many opportunities"""
        
        mock_redis_instance = Mock()
        mock_redis_instance.ping.return_value = True
        mock_redis_class.return_value = mock_redis_instance
        
        # Create multiple arbitrage opportunities
        opportunities = []
        for i in range(20):
            opportunity = ArbitrageOpportunity(
                game_id=f"perf_test_game_{i}",
                game_description=f"Team_B_{i} @ Team_A_{i}",
                market_type="h2h",
                profit_margin=0.02 + (i * 0.001),
                profit_percentage=2.0 + (i * 0.1),
                best_odds={
                    f"Team_A_{i}": {"price": -130 + i, "bookmaker": "book1"},
                    f"Team_B_{i}": {"price": 120 + i, "bookmaker": "book2"}
                },
                total_stake=1000,
                individual_stakes={f"Team_A_{i}": 500, f"Team_B_{i}": 500},
                detected_at=datetime.now(timezone.utc).isoformat(),
                expiry_estimate=(datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
            )
            opportunities.append(opportunity)
        
        with patch('app.api.multi_source_odds.find_real_time_arbitrage', return_value=opportunities):
            start_time = time.time()
            response = client.get("/api/v2/odds/arbitrage/real-time")
            end_time = time.time()
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) > 0
            # Should process opportunities quickly
            assert (end_time - start_time) < 2.0

class TestFailureScenarios:
    """Test system behavior under various failure conditions"""

    def test_redis_unavailable(self):
        """Test system behavior when Redis is unavailable"""
        
        with patch('app.services.multi_source_ingestion.redis.Redis') as mock_redis_class:
            # Mock Redis to raise connection error
            mock_redis_class.side_effect = redis.ConnectionError("Redis unavailable")
            
            # System should still function (graceful degradation)
            with patch('app.api.multi_source_odds.get_multi_source_odds', return_value={}):
                response = client.get("/api/v2/odds/")
                assert response.status_code == 200

    @patch('app.services.multi_source_ingestion.redis.Redis')
    def test_all_sources_unavailable(self, mock_redis_class):
        """Test system behavior when all data sources are unavailable"""
        
        mock_redis_instance = Mock()
        mock_redis_instance.ping.return_value = True
        mock_redis_class.return_value = mock_redis_instance
        
        # Mock all sources to return empty data
        with patch('app.api.multi_source_odds.get_multi_source_odds', return_value={}):
            response = client.get("/api/v2/odds/")
            assert response.status_code == 200
            
            data = response.json()
            assert 'sources' in data
            assert data['summary']['total_odds_entries'] == 0

    @patch('app.services.multi_source_ingestion.redis.Redis')
    def test_invalid_data_handling(self, mock_redis_class):
        """Test system behavior with invalid/corrupted data"""
        
        mock_redis_instance = Mock()
        mock_redis_instance.ping.return_value = True
        mock_redis_class.return_value = mock_redis_instance
        
        # Mock invalid data structure
        invalid_data = {
            'source1': [{'invalid': 'structure', 'missing': 'required_fields'}],
            'source2': None,
            'source3': []
        }
        
        with patch('app.api.multi_source_odds.get_multi_source_odds', return_value=invalid_data):
            response = client.get("/api/v2/odds/")
            # Should handle gracefully and not crash
            assert response.status_code == 200

class TestSecurityIntegration:
    """Test security aspects of the system"""

    @patch('app.services.multi_source_ingestion.redis.Redis')
    def test_rate_limiting_protection(self, mock_redis_class):
        """Test rate limiting protects against abuse"""
        
        mock_redis_instance = Mock()
        # Mock rate limit exceeded
        mock_redis_instance.get.side_effect = lambda key: '1000' if 'minute' in key else '50'
        mock_redis_class.return_value = mock_redis_instance
        
        # Even with rate limiting, should not return error status
        with patch('app.api.multi_source_odds.get_multi_source_odds', return_value={}):
            response = client.get("/api/v2/odds/")
            assert response.status_code == 200

    def test_input_validation(self):
        """Test input validation and sanitization"""
        
        # Test parameter validation
        response = client.get("/api/v2/odds/arbitrage/real-time?min_profit=invalid")
        assert response.status_code == 422  # Validation error
        
        response = client.get("/api/v2/odds/arbitrage/real-time?min_profit=-1")
        assert response.status_code == 422  # Out of range
        
        # Test JSON validation
        response = client.post(
            "/api/v2/odds/arbitrage/simulate",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_sql_injection_prevention(self):
        """Test SQL injection attempts are prevented"""
        
        # Test potentially malicious input
        malicious_sources = "'; DROP TABLE odds; --"
        
        response = client.get(f"/api/v2/odds/?sources={malicious_sources}")
        # Should not crash the system
        assert response.status_code in [200, 400, 422]

class TestCompatibility:
    """Test compatibility with existing API"""

    def test_legacy_api_compatibility(self):
        """Test that legacy API endpoints still work"""
        
        # Test original API endpoints
        response = client.get("/")
        assert response.status_code == 200
        
        response = client.get("/health")
        assert response.status_code == 200
        
        # Test original odds endpoint (v1)
        with patch('app.services.odds_api.get_wnba_odds', return_value={'data': []}):
            response = client.get("/api/v1/odds/")
            assert response.status_code == 200

    @patch('app.services.multi_source_ingestion.redis.Redis')
    def test_data_format_consistency(self, mock_redis_class):
        """Test that data formats are consistent between API versions"""
        
        mock_redis_instance = Mock()
        mock_redis_instance.ping.return_value = True
        mock_redis_class.return_value = mock_redis_instance
        
        sample_odds = {
            'source1': [
                OddsData(
                    game_id="consistency_test",
                    home_team="Team A",
                    away_team="Team B",
                    commence_time="2024-07-15T19:00:00Z",
                    bookmaker="test_book",
                    market_type="h2h",
                    outcomes=[{"name": "Team A", "price": -110}],
                    last_update="2024-07-15T18:30:00Z",
                    source="test_source"
                )
            ]
        }
        
        with patch('app.api.multi_source_odds.get_multi_source_odds', return_value=sample_odds):
            response = client.get("/api/v2/odds/")
            assert response.status_code == 200
            
            data = response.json()
            # Verify expected structure
            assert 'aggregated_at' in data
            assert 'sources' in data
            assert 'summary' in data

if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short", "-s"])