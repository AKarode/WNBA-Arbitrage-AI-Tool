"""
Test suite for parallel processing and concurrent arbitrage detection

This module tests the parallel processing capabilities including:
- Concurrent API calls to multiple sports
- Async/await arbitrage detection
- Rate limiting and quota management
- Performance optimization strategies
- Error handling in parallel operations

Based on research implementing:
- Real-time data processing patterns
- Distributed data aggregation
- Multi-model ensemble systems
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any

from app.core.services.parallel_arbitrage_processor import (
    ParallelArbitrageProcessor,
    ConcurrentSportsScanner,
    RateLimitManager,
    APIQuotaManager
)


class TestParallelProcessing:
    """Test cases for parallel arbitrage processing"""

    @pytest.fixture
    def processor(self):
        """Initialize parallel arbitrage processor"""
        return ParallelArbitrageProcessor(
            max_concurrent_requests=10,
            rate_limit_requests_per_second=5,
            api_quota_limit=1000,
            timeout_seconds=30
        )

    @pytest.fixture
    def sports_scanner(self):
        """Initialize concurrent sports scanner"""
        return ConcurrentSportsScanner(
            sports_config={
                "basketball_wnba": {"active": True, "priority": 1},
                "basketball_nba": {"active": True, "priority": 1}, 
                "americanfootball_nfl": {"active": True, "priority": 2},
                "baseball_mlb": {"active": True, "priority": 3},
                "icehockey_nhl": {"active": True, "priority": 3},
                "soccer_usa_mls": {"active": True, "priority": 4}
            }
        )

    @pytest.mark.asyncio
    async def test_concurrent_api_calls_basic(self, processor):
        """Test basic concurrent API calls to multiple sports"""
        
        # Mock API responses for different sports
        mock_responses = {
            "basketball_wnba": {"games": [{"id": "wnba1"}]},
            "basketball_nba": {"games": [{"id": "nba1"}]},
            "americanfootball_nfl": {"games": [{"id": "nfl1"}]}
        }
        
        async def mock_api_call(sport_key):
            # Simulate API delay
            await asyncio.sleep(0.1)
            return mock_responses.get(sport_key, {"games": []})
        
        with patch.object(processor, '_fetch_sport_odds', side_effect=mock_api_call):
            sports_list = ["basketball_wnba", "basketball_nba", "americanfootball_nfl"]
            
            start_time = time.time()
            results = await processor.fetch_multiple_sports_concurrent(sports_list)
            end_time = time.time()
            
            # Should complete in roughly 0.1 seconds (parallel) vs 0.3 (sequential)
            assert end_time - start_time < 0.2
            assert len(results) == 3
            
            # Verify all sports were processed
            assert "basketball_wnba" in results
            assert "basketball_nba" in results
            assert "americanfootball_nfl" in results

    @pytest.mark.asyncio
    async def test_concurrent_arbitrage_detection(self, processor, arbitrage_opportunity_odds):
        """Test concurrent arbitrage detection across multiple games"""
        
        # Create multiple games with arbitrage opportunities
        games_data = []
        for i in range(10):
            game = arbitrage_opportunity_odds["games"][0].copy()
            game["id"] = f"test_game_{i}"
            game["home_team"] = f"Home Team {i}"
            game["away_team"] = f"Away Team {i}"
            games_data.append(game)
        
        start_time = time.time()
        opportunities = await processor.detect_arbitrage_concurrent(games_data)
        end_time = time.time()
        
        # Should find arbitrage in all 10 games
        assert len(opportunities) == 10
        
        # Should complete faster than sequential processing
        processing_time = end_time - start_time
        assert processing_time < 1.0  # Should be very fast for 10 games
        
        # Verify all opportunities are valid
        for opp in opportunities:
            assert opp.profit_margin > 0
            assert opp.market_type is not None

    @pytest.mark.asyncio 
    async def test_rate_limiting_functionality(self, processor):
        """Test rate limiting prevents API overuse"""
        
        rate_limiter = RateLimitManager(requests_per_second=2, window_size=1.0)
        
        # Test burst of requests
        start_time = time.time()
        
        async def limited_request():
            await rate_limiter.acquire()
            return time.time()
        
        # Make 5 requests (should be rate limited to 2 per second)
        tasks = [limited_request() for _ in range(5)]
        timestamps = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should take at least 2 seconds for 5 requests at 2/second
        assert total_time >= 2.0
        
        # Verify timestamps show rate limiting
        time_diffs = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
        # Some gaps should be around 0.5 seconds (rate limit delay)
        assert any(diff >= 0.4 for diff in time_diffs)

    @pytest.mark.asyncio
    async def test_api_quota_management(self, processor):
        """Test API quota tracking and management"""
        
        quota_manager = APIQuotaManager(
            daily_limit=100,
            hourly_limit=10,
            per_request_cost=1
        )
        
        # Test quota consumption
        assert quota_manager.get_remaining_quota() == 100
        
        # Consume some quota
        await quota_manager.consume_quota(5)
        assert quota_manager.get_remaining_quota() == 95
        
        # Test quota limit enforcement
        with pytest.raises(Exception):  # Should raise quota exceeded error
            await quota_manager.consume_quota(100)  # Exceeds remaining quota
        
        # Test hourly limit
        await quota_manager.consume_quota(5)  # Total: 10 this hour
        quota_manager._current_hour_usage = 10
        
        with pytest.raises(Exception):  # Should raise hourly limit error
            await quota_manager.consume_quota(1)

    @pytest.mark.asyncio
    async def test_error_handling_in_parallel_operations(self, processor):
        """Test error handling when some API calls fail"""
        
        async def mock_api_call_with_errors(sport_key):
            if sport_key == "failing_sport":
                raise Exception("API Error")
            elif sport_key == "timeout_sport":
                await asyncio.sleep(60)  # Simulate timeout
                return {"games": []}
            else:
                return {"games": [{"id": f"{sport_key}_game"}]}
        
        with patch.object(processor, '_fetch_sport_odds', side_effect=mock_api_call_with_errors):
            sports_list = ["basketball_wnba", "failing_sport", "timeout_sport", "basketball_nba"]
            
            # Should handle errors gracefully
            results = await processor.fetch_multiple_sports_concurrent(sports_list)
            
            # Should get results for successful calls only
            assert "basketball_wnba" in results
            assert "basketball_nba" in results
            
            # Failed calls should be handled
            assert "failing_sport" not in results or results["failing_sport"] is None
            assert "timeout_sport" not in results or results["timeout_sport"] is None

    def test_thread_pool_performance(self, processor, performance_test_data):
        """Test thread pool performance for CPU-intensive calculations"""
        
        def calculate_arbitrage_cpu_intensive(game_data):
            """Simulate CPU-intensive arbitrage calculation"""
            import math
            
            # Simulate complex calculation
            for _ in range(1000):
                math.sqrt(game_data.get("id", 1).__hash__())
            
            # Return mock arbitrage result
            return {
                "game_id": game_data.get("id"),
                "profit_margin": 2.5,
                "calculation_complete": True
            }
        
        games = performance_test_data["games"][:20]  # Test with 20 games
        
        # Test sequential processing
        start_time = time.time()
        sequential_results = []
        for game in games:
            result = calculate_arbitrage_cpu_intensive(game)
            sequential_results.append(result)
        sequential_time = time.time() - start_time
        
        # Test parallel processing with thread pool
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_game = {
                executor.submit(calculate_arbitrage_cpu_intensive, game): game 
                for game in games
            }
            parallel_results = []
            for future in as_completed(future_to_game):
                result = future.result()
                parallel_results.append(result)
        parallel_time = time.time() - start_time
        
        # Parallel should be faster than sequential
        assert parallel_time < sequential_time
        assert len(parallel_results) == len(sequential_results)
        
        # Calculate speedup ratio
        speedup = sequential_time / parallel_time
        print(f"Thread pool speedup: {speedup:.2f}x")

    @pytest.mark.asyncio
    async def test_priority_based_processing(self, sports_scanner):
        """Test priority-based processing of sports"""
        
        # Mock API call times based on sport priority
        async def mock_prioritized_api_call(sport_key):
            priority = sports_scanner.sports_config[sport_key]["priority"]
            # Higher priority (lower number) = faster processing
            delay = priority * 0.1
            await asyncio.sleep(delay)
            return {"sport": sport_key, "games": [{"id": f"{sport_key}_game"}]}
        
        with patch.object(sports_scanner, '_fetch_sport_data', side_effect=mock_prioritized_api_call):
            start_time = time.time()
            
            # Process all sports with priority ordering
            results = await sports_scanner.scan_all_sports_prioritized()
            
            end_time = time.time()
            
            # Verify results contain all sports
            assert len(results) == 6
            
            # Verify priority ordering is respected
            result_order = list(results.keys())
            
            # Priority 1 sports should be processed first
            priority_1_sports = ["basketball_wnba", "basketball_nba"]
            for sport in priority_1_sports:
                assert sport in result_order[:2]

    @pytest.mark.asyncio
    async def test_dynamic_concurrency_adjustment(self, processor):
        """Test dynamic adjustment of concurrency based on system load"""
        
        # Mock system load monitoring
        async def mock_system_load():
            return {
                "cpu_percent": 75.0,
                "memory_percent": 60.0,
                "active_connections": 8
            }
        
        with patch.object(processor, '_get_system_load', side_effect=mock_system_load):
            # Should reduce concurrency under high load
            optimal_concurrency = await processor.calculate_optimal_concurrency()
            
            # With 75% CPU, should reduce from max of 10
            assert optimal_concurrency < processor.max_concurrent_requests
            assert optimal_concurrency >= 1
        
        # Test with low system load
        async def mock_low_system_load():
            return {
                "cpu_percent": 25.0,
                "memory_percent": 30.0, 
                "active_connections": 2
            }
        
        with patch.object(processor, '_get_system_load', side_effect=mock_low_system_load):
            # Should allow higher concurrency with low load
            optimal_concurrency = await processor.calculate_optimal_concurrency()
            
            # With low load, should use near maximum concurrency
            assert optimal_concurrency >= processor.max_concurrent_requests * 0.8

    @pytest.mark.asyncio
    async def test_circuit_breaker_pattern(self, processor):
        """Test circuit breaker pattern for failing APIs"""
        
        circuit_breaker = processor.circuit_breaker
        
        # Simulate multiple API failures
        for _ in range(5):
            await circuit_breaker.record_failure("test_api")
        
        # Circuit should be open after failures
        assert circuit_breaker.is_open("test_api")
        
        # Requests should be rejected while circuit is open
        with pytest.raises(Exception):  # Circuit breaker exception
            await processor._fetch_sport_odds_with_circuit_breaker("test_sport")
        
        # Test circuit breaker recovery
        await asyncio.sleep(circuit_breaker.recovery_timeout)
        await circuit_breaker.record_success("test_api")
        
        # Circuit should be closed after success
        assert not circuit_breaker.is_open("test_api")

    @pytest.mark.asyncio
    async def test_memory_efficient_processing(self, processor):
        """Test memory-efficient processing of large datasets"""
        
        # Create large dataset
        large_dataset = []
        for i in range(1000):
            game = {
                "id": f"game_{i}",
                "home_team": f"Home {i}",
                "away_team": f"Away {i}",
                "bookmakers": [
                    {
                        "key": f"book_{j}",
                        "markets": [{"key": "h2h", "outcomes": [
                            {"name": f"Home {i}", "price": 1.90 + (i % 10) * 0.01},
                            {"name": f"Away {i}", "price": 1.95 + (i % 8) * 0.01}
                        ]}]
                    }
                    for j in range(3)
                ]
            }
            large_dataset.append(game)
        
        # Process in chunks to manage memory
        chunk_size = 100
        all_opportunities = []
        
        start_time = time.time()
        
        for i in range(0, len(large_dataset), chunk_size):
            chunk = large_dataset[i:i + chunk_size]
            chunk_opportunities = await processor.process_games_chunk(chunk)
            all_opportunities.extend(chunk_opportunities)
            
            # Simulate garbage collection between chunks
            import gc
            gc.collect()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process efficiently without memory issues
        games_per_second = len(large_dataset) / processing_time
        print(f"Processed {games_per_second:.2f} games per second")
        
        # Should complete within reasonable time
        assert processing_time < 30.0  # 30 seconds for 1000 games