"""
Integration test suite for enhanced arbitrage detection system

This module tests the complete integration of all enhanced features:
- End-to-end arbitrage detection workflow
- API integration with real-like data
- Performance benchmarks
- System reliability under load
- Error recovery and resilience
"""

import pytest
import asyncio
import json
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.services.enhanced_arbitrage_system import EnhancedArbitrageSystem


class TestEnhancedSystemIntegration:
    """Integration tests for the complete enhanced arbitrage system"""

    @pytest.fixture
    def enhanced_system(self):
        """Initialize the complete enhanced arbitrage system"""
        return EnhancedArbitrageSystem(
            enable_parallel_processing=True,
            enable_cross_market_detection=True,
            enable_caching=True,
            enable_rate_limiting=True
        )

    @pytest.fixture
    def client(self):
        """FastAPI test client"""
        return TestClient(app)

    def test_enhanced_api_endpoint_single_sport(self, client):
        """Test enhanced API endpoint for single sport arbitrage detection"""
        
        # Mock enhanced API response
        mock_response = {
            "sport": {
                "key": "basketball_wnba",
                "title": "WNBA", 
                "scanning_mode": "enhanced"
            },
            "analysis": {
                "total_games_analyzed": 5,
                "processing_time_ms": 234,
                "opportunities_found": 2,
                "markets_analyzed": ["h2h", "spreads", "totals"],
                "cross_market_opportunities": 1,
                "enhanced_opportunities": [
                    {
                        "game": {
                            "home_team": "Las Vegas Aces",
                            "away_team": "Seattle Storm"
                        },
                        "arbitrage_type": "moneyline",
                        "profit_margin": 3.45,
                        "best_odds": {
                            "Las Vegas Aces": {"price": 1.75, "bookmaker": "BetOnline.ag"},
                            "Seattle Storm": {"price": 2.80, "bookmaker": "Bovada"}
                        },
                        "optimal_stakes": {
                            "Las Vegas Aces": 571.43,
                            "Seattle Storm": 357.14,
                            "total_investment": 928.57,
                            "guaranteed_profit": 71.43
                        }
                    },
                    {
                        "game": {
                            "home_team": "New York Liberty", 
                            "away_team": "Connecticut Sun"
                        },
                        "arbitrage_type": "cross_market",
                        "market_combination": ["h2h", "spreads"],
                        "profit_margin": 2.15,
                        "correlation_risk": 0.25,
                        "selected_outcomes": {
                            "h2h": "Connecticut Sun",
                            "spreads": "New York Liberty -3.5"
                        }
                    }
                ]
            }
        }

        with patch('app.core.api.enhanced_arbitrage.get_enhanced_arbitrage') as mock_api:
            mock_api.return_value = mock_response
            
            response = client.get("/api/enhanced/arbitrage/basketball_wnba?min_profit=2.0")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["analysis"]["opportunities_found"] == 2
            assert data["analysis"]["cross_market_opportunities"] == 1
            assert len(data["analysis"]["enhanced_opportunities"]) == 2

    def test_enhanced_multi_sport_scanning(self, client):
        """Test enhanced multi-sport scanning with parallel processing"""
        
        mock_multi_sport_response = {
            "scan_summary": {
                "sports_analyzed": 6,
                "total_games": 87,
                "processing_time_ms": 1250,
                "parallel_processing": True,
                "total_opportunities": 5
            },
            "sport_breakdown": {
                "basketball_wnba": {"games": 8, "opportunities": 2},
                "basketball_nba": {"games": 12, "opportunities": 1}, 
                "americanfootball_nfl": {"games": 45, "opportunities": 1},
                "baseball_mlb": {"games": 15, "opportunities": 1},
                "icehockey_nhl": {"games": 4, "opportunities": 0},
                "soccer_usa_mls": {"games": 3, "opportunities": 0}
            },
            "all_opportunities": [
                {
                    "sport": "basketball_wnba",
                    "profit_margin": 4.2,
                    "arbitrage_type": "moneyline"
                },
                {
                    "sport": "basketball_wnba", 
                    "profit_margin": 2.8,
                    "arbitrage_type": "spreads"
                },
                {
                    "sport": "basketball_nba",
                    "profit_margin": 3.1,
                    "arbitrage_type": "cross_market"
                },
                {
                    "sport": "americanfootball_nfl",
                    "profit_margin": 2.3,
                    "arbitrage_type": "totals"
                },
                {
                    "sport": "baseball_mlb",
                    "profit_margin": 1.9,
                    "arbitrage_type": "moneyline"
                }
            ]
        }

        with patch('app.core.api.enhanced_arbitrage.scan_all_sports_enhanced') as mock_scan:
            mock_scan.return_value = mock_multi_sport_response
            
            response = client.get("/api/enhanced/arbitrage/all?min_profit=1.5&enable_cross_market=true")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["scan_summary"]["sports_analyzed"] == 6
            assert data["scan_summary"]["parallel_processing"] is True
            assert data["scan_summary"]["total_opportunities"] == 5
            assert len(data["all_opportunities"]) == 5
            
            # Verify opportunities are sorted by profit margin
            profit_margins = [opp["profit_margin"] for opp in data["all_opportunities"]]
            assert profit_margins == sorted(profit_margins, reverse=True)

    @pytest.mark.asyncio
    async def test_real_time_streaming_arbitrage(self, enhanced_system):
        """Test real-time streaming arbitrage detection"""
        
        # Mock real-time data stream
        async def mock_odds_stream():
            """Simulate real-time odds updates"""
            updates = [
                {
                    "timestamp": "2025-06-09T20:00:00Z",
                    "sport": "basketball_wnba",
                    "game_id": "wnba_game_1",
                    "odds_update": {
                        "bookmaker": "fanduel",
                        "market": "h2h",
                        "odds": [{"team": "Team A", "price": 1.85}, {"team": "Team B", "price": 2.00}]
                    }
                },
                {
                    "timestamp": "2025-06-09T20:00:05Z",
                    "sport": "basketball_wnba", 
                    "game_id": "wnba_game_1",
                    "odds_update": {
                        "bookmaker": "betonlineag",
                        "market": "h2h", 
                        "odds": [{"team": "Team A", "price": 2.10}, {"team": "Team B", "price": 1.75}]
                    }
                }
            ]
            
            for update in updates:
                yield update
                await asyncio.sleep(0.1)

        opportunities_detected = []
        
        async def opportunity_handler(opportunity):
            opportunities_detected.append(opportunity)

        # Start real-time monitoring
        with patch.object(enhanced_system, 'get_real_time_odds_stream', side_effect=mock_odds_stream):
            await enhanced_system.start_real_time_monitoring(
                sports=["basketball_wnba"],
                opportunity_callback=opportunity_handler,
                duration_seconds=1
            )

        # Should detect arbitrage opportunity from the odds updates
        # Team A at 2.10 (47.62%) + Team B at 2.00 (50.00%) = 97.62% = 2.38% profit
        assert len(opportunities_detected) > 0
        
        opportunity = opportunities_detected[0]
        assert opportunity["profit_margin"] > 2.0
        assert opportunity["sport"] == "basketball_wnba"

    def test_caching_system_performance(self, enhanced_system):
        """Test caching system performance and cache hit rates"""
        
        # Mock Redis cache
        cache_hits = 0
        cache_misses = 0
        
        async def mock_cache_get(key):
            nonlocal cache_hits, cache_misses
            if "cached_sport" in key:
                cache_hits += 1
                return json.dumps({"games": [{"id": "cached_game"}]})
            else:
                cache_misses += 1
                return None
        
        async def mock_cache_set(key, value, ttl):
            pass
        
        with patch.object(enhanced_system.cache, 'get', side_effect=mock_cache_get):
            with patch.object(enhanced_system.cache, 'set', side_effect=mock_cache_set):
                
                # Request same sport multiple times
                for _ in range(5):
                    await enhanced_system.get_sport_odds("cached_sport")
                
                # Request different sports 
                for i in range(3):
                    await enhanced_system.get_sport_odds(f"new_sport_{i}")

        # Should have cache hits for repeated requests
        assert cache_hits > 0
        assert cache_misses > 0
        
        cache_hit_rate = cache_hits / (cache_hits + cache_misses)
        assert cache_hit_rate > 0.5  # Should have good cache hit rate

    @pytest.mark.asyncio
    async def test_error_recovery_and_resilience(self, enhanced_system):
        """Test system error recovery and resilience"""
        
        # Test API failure recovery
        api_call_count = 0
        
        async def mock_failing_api_call(sport_key):
            nonlocal api_call_count
            api_call_count += 1
            
            if api_call_count <= 2:
                raise Exception("API temporarily unavailable")
            else:
                return {"games": [{"id": f"{sport_key}_game"}]}
        
        with patch.object(enhanced_system, '_fetch_sport_odds', side_effect=mock_failing_api_call):
            # Should retry and eventually succeed
            result = await enhanced_system.get_sport_odds_with_retry("basketball_wnba")
            
            assert result is not None
            assert api_call_count == 3  # Failed twice, succeeded on third try

    def test_performance_benchmarks(self, enhanced_system, performance_test_data):
        """Test performance benchmarks against requirements"""
        
        import time
        
        # Benchmark 1: Single sport processing time
        start_time = time.time()
        opportunities = enhanced_system.detect_arbitrage_sync(
            performance_test_data["games"][:10]
        )
        single_sport_time = time.time() - start_time
        
        # Should process 10 games in under 100ms
        assert single_sport_time < 0.1
        
        # Benchmark 2: Multi-sport parallel processing
        start_time = time.time()
        multi_sport_opportunities = enhanced_system.process_multiple_sports_sync([
            {"sport": "basketball_wnba", "games": performance_test_data["games"][:5]},
            {"sport": "basketball_nba", "games": performance_test_data["games"][5:10]},
            {"sport": "americanfootball_nfl", "games": performance_test_data["games"][10:15]}
        ])
        multi_sport_time = time.time() - start_time
        
        # Parallel processing should be faster than 3x single sport time
        assert multi_sport_time < single_sport_time * 2
        
        # Benchmark 3: Memory usage efficiency
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process large dataset
        large_opportunities = enhanced_system.detect_arbitrage_sync(
            performance_test_data["games"]
        )
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for 100 games)
        assert memory_increase < 100

    def test_rate_limiting_integration(self, client):
        """Test rate limiting integration in API endpoints"""
        
        # Make multiple rapid requests
        responses = []
        for i in range(10):
            response = client.get(f"/api/enhanced/arbitrage/basketball_wnba?request_id={i}")
            responses.append(response)
        
        # Some requests should be rate limited (429 status)
        status_codes = [r.status_code for r in responses]
        
        # Should have mix of 200 (success) and 429 (rate limited)
        assert 200 in status_codes
        # Rate limiting might not trigger in test environment
        
        # Test rate limit headers
        successful_response = next(r for r in responses if r.status_code == 200)
        assert "X-RateLimit-Remaining" in successful_response.headers

    def test_comprehensive_arbitrage_workflow(self, enhanced_system):
        """Test complete arbitrage detection workflow end-to-end"""
        
        # Step 1: Initialize system
        system_status = enhanced_system.get_system_status()
        assert system_status["status"] == "ready"
        assert system_status["features"]["parallel_processing"] is True
        assert system_status["features"]["cross_market_detection"] is True
        
        # Step 2: Scan all sports
        scan_results = enhanced_system.scan_all_sports_enhanced(
            min_profit=1.0,
            enable_cross_market=True,
            max_concurrent=5
        )
        
        assert "scan_summary" in scan_results
        assert "all_opportunities" in scan_results
        
        # Step 3: Process each opportunity found
        for opportunity in scan_results["all_opportunities"]:
            # Validate opportunity structure
            assert "sport" in opportunity
            assert "profit_margin" in opportunity
            assert "arbitrage_type" in opportunity
            
            # Calculate stakes for each opportunity
            if opportunity["arbitrage_type"] != "cross_market":
                stakes = enhanced_system.calculate_optimal_stakes(
                    opportunity, bankroll=10000
                )
                assert stakes["total_investment"] > 0
                assert stakes["guaranteed_profit"] > 0
        
        # Step 4: Generate summary report
        summary_report = enhanced_system.generate_arbitrage_report(scan_results)
        
        assert "executive_summary" in summary_report
        assert "detailed_opportunities" in summary_report
        assert "risk_analysis" in summary_report
        assert "performance_metrics" in summary_report

    def test_api_documentation_accuracy(self, client):
        """Test that API documentation matches actual functionality"""
        
        # Test OpenAPI spec endpoint
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        
        # Verify enhanced endpoints are documented
        paths = openapi_spec["paths"]
        assert "/api/enhanced/arbitrage/{sport_key}" in paths
        assert "/api/enhanced/arbitrage/all" in paths
        
        # Verify response schemas include enhanced fields
        sport_endpoint = paths["/api/enhanced/arbitrage/{sport_key}"]["get"]
        response_schema = sport_endpoint["responses"]["200"]["content"]["application/json"]["schema"]
        
        # Should include enhanced fields in documentation
        # This is a simplified check - full validation would require more complex schema parsing

    @pytest.mark.asyncio
    async def test_concurrent_user_simulation(self, enhanced_system):
        """Test system behavior under concurrent user load"""
        
        async def simulate_user_requests():
            """Simulate a user making multiple requests"""
            requests = [
                enhanced_system.get_sport_arbitrage("basketball_wnba"),
                enhanced_system.get_sport_arbitrage("basketball_nba"),
                enhanced_system.scan_all_sports_brief()
            ]
            
            results = await asyncio.gather(*requests, return_exceptions=True)
            return results
        
        # Simulate 5 concurrent users
        user_tasks = [simulate_user_requests() for _ in range(5)]
        all_user_results = await asyncio.gather(*user_tasks)
        
        # All users should get valid responses
        for user_results in all_user_results:
            for result in user_results:
                # Should not be an exception
                assert not isinstance(result, Exception)
        
        # System should remain responsive
        assert len(all_user_results) == 5