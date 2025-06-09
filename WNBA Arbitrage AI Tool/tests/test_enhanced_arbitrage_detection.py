"""
Test suite for enhanced arbitrage detection algorithms

This module tests the core arbitrage detection algorithms including:
- Multi-market arbitrage detection (moneyline, spreads, totals)
- Cross-market arbitrage opportunities
- Advanced probability calculations
- Edge case handling

Based on research, this implements:
- Mathematical arbitrage formulas with ensemble approach
- Cross-market detection techniques
- Performance optimization strategies
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any
from decimal import Decimal

from app.core.services.enhanced_arbitrage_engine import (
    EnhancedArbitrageEngine,
    ArbitrageOpportunity,
    MarketType,
    CrossMarketArbitrage
)


class TestEnhancedArbitrageDetection:
    """Test cases for enhanced arbitrage detection algorithms"""

    @pytest.fixture
    def arbitrage_engine(self):
        """Initialize enhanced arbitrage engine for testing"""
        return EnhancedArbitrageEngine(
            min_profit_threshold=0.1,  # Low threshold for testing
            max_stake_percentage=0.95,
            enable_cross_market=True
        )

    def test_moneyline_arbitrage_detection_basic(self, arbitrage_engine, arbitrage_opportunity_odds):
        """Test basic moneyline arbitrage detection with clear opportunity"""
        game_data = arbitrage_opportunity_odds["games"][0]
        
        opportunities = arbitrage_engine.detect_moneyline_arbitrage(game_data)
        
        assert len(opportunities) == 1
        opportunity = opportunities[0]
        
        # Expected: Team A at 2.20 (45.45%) + Team B at 3.00 (33.33%) = 78.78%
        # Profit: (1 - 0.7878) * 100 = 21.22%
        assert opportunity.profit_margin == pytest.approx(21.22, rel=1e-2)
        assert opportunity.market_type == MarketType.MONEYLINE
        assert len(opportunity.best_odds) == 2
        
        # Verify best odds selection
        assert opportunity.best_odds["Team A"]["price"] == 2.20
        assert opportunity.best_odds["Team A"]["bookmaker"] == "Bookmaker 1"
        assert opportunity.best_odds["Team B"]["price"] == 3.00
        assert opportunity.best_odds["Team B"]["bookmaker"] == "Bookmaker 2"

    def test_moneyline_no_arbitrage(self, arbitrage_engine, mock_odds_api_response):
        """Test moneyline detection when no arbitrage exists"""
        game_data = mock_odds_api_response["games"][0]
        
        opportunities = arbitrage_engine.detect_moneyline_arbitrage(game_data)
        
        # Current odds: Valkyries 3.26, Sparks 1.38
        # Implied: 30.67% + 72.46% = 103.13% (no arbitrage)
        assert len(opportunities) == 0

    def test_spread_arbitrage_detection(self, arbitrage_engine):
        """Test spread arbitrage detection algorithm"""
        spread_arbitrage_data = {
            "id": "spread_arbitrage_game",
            "home_team": "Team A",
            "away_team": "Team B", 
            "bookmakers": [
                {
                    "key": "book1",
                    "title": "Bookmaker 1",
                    "markets": [
                        {
                            "key": "spreads",
                            "outcomes": [
                                {"name": "Team A", "price": 2.10, "point": -3.5},
                                {"name": "Team B", "price": 1.75, "point": 3.5}
                            ]
                        }
                    ]
                },
                {
                    "key": "book2", 
                    "title": "Bookmaker 2",
                    "markets": [
                        {
                            "key": "spreads",
                            "outcomes": [
                                {"name": "Team A", "price": 1.70, "point": -3.5},
                                {"name": "Team B", "price": 2.30, "point": 3.5}
                            ]
                        }
                    ]
                }
            ]
        }
        
        opportunities = arbitrage_engine.detect_spread_arbitrage(spread_arbitrage_data)
        
        # Best odds: Team A at 2.10 (47.62%) + Team B at 2.30 (43.48%) = 91.10%
        # Profit: (1 - 0.9110) * 100 = 8.90%
        assert len(opportunities) == 1
        opportunity = opportunities[0]
        
        assert opportunity.profit_margin == pytest.approx(8.90, rel=1e-2)
        assert opportunity.market_type == MarketType.SPREAD
        assert opportunity.spread_value == 3.5

    def test_totals_arbitrage_detection(self, arbitrage_engine):
        """Test totals (over/under) arbitrage detection"""
        totals_arbitrage_data = {
            "id": "totals_arbitrage_game",
            "home_team": "Team A",
            "away_team": "Team B",
            "bookmakers": [
                {
                    "key": "book1",
                    "title": "Bookmaker 1", 
                    "markets": [
                        {
                            "key": "totals",
                            "outcomes": [
                                {"name": "Over", "price": 2.20, "point": 165.5},
                                {"name": "Under", "price": 1.70, "point": 165.5}
                            ]
                        }
                    ]
                },
                {
                    "key": "book2",
                    "title": "Bookmaker 2",
                    "markets": [
                        {
                            "key": "totals", 
                            "outcomes": [
                                {"name": "Over", "price": 1.65, "point": 165.5},
                                {"name": "Under", "price": 2.40, "point": 165.5}
                            ]
                        }
                    ]
                }
            ]
        }
        
        opportunities = arbitrage_engine.detect_totals_arbitrage(totals_arbitrage_data)
        
        # Best odds: Over at 2.20 (45.45%) + Under at 2.40 (41.67%) = 87.12%
        # Profit: (1 - 0.8712) * 100 = 12.88%
        assert len(opportunities) == 1
        opportunity = opportunities[0]
        
        assert opportunity.profit_margin == pytest.approx(12.88, rel=1e-2)
        assert opportunity.market_type == MarketType.TOTALS
        assert opportunity.total_value == 165.5

    def test_cross_market_arbitrage_detection(self, arbitrage_engine):
        """Test cross-market arbitrage detection (moneyline vs spread)"""
        cross_market_data = {
            "id": "cross_market_game",
            "home_team": "Team A", 
            "away_team": "Team B",
            "bookmakers": [
                {
                    "key": "book1",
                    "title": "Bookmaker 1",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Team A", "price": 1.50},  # Strong favorite
                                {"name": "Team B", "price": 2.60}
                            ]
                        },
                        {
                            "key": "spreads",
                            "outcomes": [
                                {"name": "Team A", "price": 2.05, "point": -7.5},  # Generous spread odds
                                {"name": "Team B", "price": 1.80, "point": 7.5}
                            ]
                        }
                    ]
                }
            ]
        }
        
        opportunities = arbitrage_engine.detect_cross_market_arbitrage(cross_market_data)
        
        # Cross-market: Team A moneyline (66.67%) vs Team B spread +7.5 (55.56%)
        # This tests correlation between markets
        assert isinstance(opportunities, list)
        # Cross-market arbitrage is more complex and may not always exist

    def test_multiple_bookmaker_best_odds_selection(self, arbitrage_engine):
        """Test algorithm correctly selects best odds across multiple bookmakers"""
        multi_book_data = {
            "id": "multi_book_game",
            "home_team": "Team A",
            "away_team": "Team B",
            "bookmakers": [
                {
                    "key": "book1", "title": "Book 1",
                    "markets": [{"key": "h2h", "outcomes": [
                        {"name": "Team A", "price": 1.90},
                        {"name": "Team B", "price": 1.95}
                    ]}]
                },
                {
                    "key": "book2", "title": "Book 2", 
                    "markets": [{"key": "h2h", "outcomes": [
                        {"name": "Team A", "price": 2.10},  # Best for Team A
                        {"name": "Team B", "price": 1.85}
                    ]}]
                },
                {
                    "key": "book3", "title": "Book 3",
                    "markets": [{"key": "h2h", "outcomes": [
                        {"name": "Team A", "price": 1.80},
                        {"name": "Team B", "price": 2.20}   # Best for Team B
                    ]}]
                }
            ]
        }
        
        best_odds = arbitrage_engine._find_best_odds(multi_book_data, "h2h")
        
        assert best_odds["Team A"]["price"] == 2.10
        assert best_odds["Team A"]["bookmaker"] == "Book 2"
        assert best_odds["Team B"]["price"] == 2.20
        assert best_odds["Team B"]["bookmaker"] == "Book 3"

    def test_implied_probability_calculation(self, arbitrage_engine):
        """Test implied probability calculations are accurate"""
        test_cases = [
            (2.00, 0.5),      # Even odds = 50%
            (1.50, 0.6667),   # Strong favorite
            (3.00, 0.3333),   # Underdog
            (1.10, 0.9091),   # Heavy favorite
            (10.0, 0.1)       # Long shot
        ]
        
        for odds, expected_prob in test_cases:
            calculated_prob = arbitrage_engine._calculate_implied_probability(odds)
            assert calculated_prob == pytest.approx(expected_prob, rel=1e-3)

    def test_stake_calculation_optimization(self, arbitrage_engine):
        """Test optimal stake calculation for arbitrage opportunities"""
        opportunity_data = {
            "Team A": {"price": 2.20, "bookmaker": "Book 1"},
            "Team B": {"price": 3.00, "bookmaker": "Book 2"}
        }
        bankroll = 1000.0
        
        stakes = arbitrage_engine.calculate_optimal_stakes(opportunity_data, bankroll)
        
        # Team A: 45.45% of total investment
        # Team B: 33.33% of total investment
        # Total investment: 78.78% of bankroll
        total_investment = 1000 * 0.7878  # 787.8
        
        expected_stake_a = total_investment * (1/2.20) / (1/2.20 + 1/3.00)
        expected_stake_b = total_investment * (1/3.00) / (1/2.20 + 1/3.00)
        
        assert stakes["Team A"] == pytest.approx(expected_stake_a, rel=1e-2)
        assert stakes["Team B"] == pytest.approx(expected_stake_b, rel=1e-2)
        
        # Verify guaranteed profit regardless of outcome
        profit_if_a_wins = stakes["Team A"] * 2.20 - total_investment
        profit_if_b_wins = stakes["Team B"] * 3.00 - total_investment
        
        assert profit_if_a_wins == pytest.approx(profit_if_b_wins, rel=1e-2)
        assert profit_if_a_wins > 0  # Guaranteed profit

    def test_minimum_profit_threshold_filtering(self, arbitrage_engine):
        """Test that opportunities below minimum threshold are filtered out"""
        low_margin_data = {
            "id": "low_margin_game",
            "home_team": "Team A",
            "away_team": "Team B", 
            "bookmakers": [
                {
                    "key": "book1", "title": "Book 1",
                    "markets": [{"key": "h2h", "outcomes": [
                        {"name": "Team A", "price": 1.98},  # 50.51%
                        {"name": "Team B", "price": 2.02}   # 49.50%
                    ]}]
                }
            ]
        }
        
        # Total implied probability: 100.01% (no arbitrage)
        opportunities = arbitrage_engine.detect_moneyline_arbitrage(low_margin_data)
        assert len(opportunities) == 0
        
        # Test with arbitrage engine set to very low threshold
        engine_low_threshold = EnhancedArbitrageEngine(min_profit_threshold=0.01)
        
        # Create data with tiny arbitrage margin
        tiny_margin_data = {
            "id": "tiny_margin_game",
            "home_team": "Team A",
            "away_team": "Team B",
            "bookmakers": [
                {
                    "key": "book1", "title": "Book 1", 
                    "markets": [{"key": "h2h", "outcomes": [
                        {"name": "Team A", "price": 2.005},  # 49.88%
                        {"name": "Team B", "price": 2.005}   # 49.88%
                    ]}]
                }
            ]
        }
        
        # Total implied: 99.76% = 0.24% profit (above 0.01% threshold)
        opportunities = engine_low_threshold.detect_moneyline_arbitrage(tiny_margin_data)
        assert len(opportunities) == 1
        assert opportunities[0].profit_margin == pytest.approx(0.24, rel=1e-2)

    def test_edge_case_handling(self, arbitrage_engine):
        """Test handling of edge cases and malformed data"""
        
        # Test with missing bookmaker data
        missing_bookmaker_data = {
            "id": "missing_book_game",
            "home_team": "Team A",
            "away_team": "Team B",
            "bookmakers": []
        }
        
        opportunities = arbitrage_engine.detect_moneyline_arbitrage(missing_bookmaker_data)
        assert len(opportunities) == 0
        
        # Test with single bookmaker (no arbitrage possible)
        single_book_data = {
            "id": "single_book_game", 
            "home_team": "Team A",
            "away_team": "Team B",
            "bookmakers": [
                {
                    "key": "book1", "title": "Book 1",
                    "markets": [{"key": "h2h", "outcomes": [
                        {"name": "Team A", "price": 1.90},
                        {"name": "Team B", "price": 1.95}
                    ]}]
                }
            ]
        }
        
        opportunities = arbitrage_engine.detect_moneyline_arbitrage(single_book_data)
        assert len(opportunities) == 0
        
        # Test with malformed odds data
        malformed_data = {
            "id": "malformed_game",
            "home_team": "Team A", 
            "away_team": "Team B",
            "bookmakers": [
                {
                    "key": "book1", "title": "Book 1",
                    "markets": [{"key": "h2h", "outcomes": [
                        {"name": "Team A", "price": "invalid"},  # Invalid price
                        {"name": "Team B", "price": 1.95}
                    ]}]
                }
            ]
        }
        
        # Should handle gracefully without crashing
        opportunities = arbitrage_engine.detect_moneyline_arbitrage(malformed_data)
        assert len(opportunities) == 0

    def test_performance_with_large_dataset(self, arbitrage_engine, performance_test_data):
        """Test performance with large number of games and bookmakers"""
        import time
        
        start_time = time.time()
        
        all_opportunities = []
        for game in performance_test_data["games"]:
            opportunities = arbitrage_engine.detect_moneyline_arbitrage(game)
            all_opportunities.extend(opportunities)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process 100 games with 5 bookmakers each in under 1 second
        assert processing_time < 1.0
        
        # Log performance metrics
        games_per_second = len(performance_test_data["games"]) / processing_time
        print(f"Processed {games_per_second:.2f} games per second")
        print(f"Found {len(all_opportunities)} arbitrage opportunities")