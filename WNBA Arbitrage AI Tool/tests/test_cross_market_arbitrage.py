"""
Test suite for cross-market arbitrage detection

This module tests advanced cross-market arbitrage strategies including:
- Moneyline vs Spread arbitrage
- Spread vs Totals arbitrage  
- Multi-outcome correlation analysis
- Advanced probability modeling
- Cross-bookmaker market inefficiency detection

Based on research implementing:
- Cross-market arbitrage detection techniques
- Behavioral pattern analysis
- Machine learning detection patterns
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from typing import Dict, List, Any
from decimal import Decimal

from app.core.services.cross_market_analyzer import (
    CrossMarketAnalyzer,
    MarketCorrelationModel,
    CrossMarketOpportunity,
    CorrelationMatrix
)


class TestCrossMarketArbitrage:
    """Test cases for cross-market arbitrage detection"""

    @pytest.fixture
    def analyzer(self):
        """Initialize cross-market analyzer"""
        return CrossMarketAnalyzer(
            correlation_threshold=0.85,
            min_profit_margin=0.5,
            max_correlation_risk=0.15
        )

    @pytest.fixture 
    def correlation_model(self):
        """Initialize market correlation model"""
        return MarketCorrelationModel()

    def test_moneyline_vs_spread_arbitrage(self, analyzer):
        """Test arbitrage between moneyline and spread markets"""
        
        cross_market_data = {
            "id": "ml_spread_arbitrage",
            "home_team": "Lakers",
            "away_team": "Warriors",
            "bookmakers": [
                {
                    "key": "book1",
                    "title": "Bookmaker 1",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Lakers", "price": 1.45},     # Strong favorite (68.97%)
                                {"name": "Warriors", "price": 2.75}    # Underdog (36.36%)
                            ]
                        },
                        {
                            "key": "spreads", 
                            "outcomes": [
                                {"name": "Lakers", "price": 2.10, "point": -8.5},   # Generous spread odds
                                {"name": "Warriors", "price": 1.75, "point": 8.5}
                            ]
                        }
                    ]
                }
            ]
        }
        
        opportunities = analyzer.detect_moneyline_spread_arbitrage(cross_market_data)
        
        # Should detect opportunity: Warriors ML + Lakers spread
        # Warriors ML at 2.75 (36.36%) + Lakers -8.5 at 2.10 (47.62%) = 83.98%
        assert len(opportunities) > 0
        
        opportunity = opportunities[0]
        assert opportunity.market_combination == ["h2h", "spreads"]
        assert opportunity.profit_margin > 0
        assert "Warriors" in opportunity.selected_outcomes
        assert "Lakers" in opportunity.selected_outcomes

    def test_spread_vs_totals_correlation(self, analyzer, correlation_model):
        """Test correlation analysis between spread and totals markets"""
        
        spread_totals_data = {
            "id": "spread_totals_game",
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
                                {"name": "Team A", "price": 1.90, "point": -3.5},
                                {"name": "Team B", "price": 1.95, "point": 3.5}
                            ]
                        },
                        {
                            "key": "totals",
                            "outcomes": [
                                {"name": "Over", "price": 2.20, "point": 210.5},
                                {"name": "Under", "price": 1.70, "point": 210.5}
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Calculate correlation between spread and totals
        correlation = correlation_model.calculate_spread_totals_correlation(spread_totals_data)
        
        # Verify correlation analysis
        assert isinstance(correlation, float)
        assert -1.0 <= correlation <= 1.0
        
        # Test cross-market opportunity detection
        opportunities = analyzer.detect_spread_totals_arbitrage(spread_totals_data)
        
        # May or may not find opportunities depending on correlation
        assert isinstance(opportunities, list)

    def test_three_way_market_arbitrage(self, analyzer):
        """Test arbitrage across three different markets simultaneously"""
        
        three_way_data = {
            "id": "three_way_game",
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
                                {"name": "Team A", "price": 1.80},
                                {"name": "Team B", "price": 2.05}
                            ]
                        },
                        {
                            "key": "spreads",
                            "outcomes": [
                                {"name": "Team A", "price": 2.20, "point": -2.5},
                                {"name": "Team B", "price": 1.70, "point": 2.5}
                            ]
                        },
                        {
                            "key": "totals", 
                            "outcomes": [
                                {"name": "Over", "price": 2.30, "point": 200.5},
                                {"name": "Under", "price": 1.65, "point": 200.5}
                            ]
                        }
                    ]
                }
            ]
        }
        
        opportunities = analyzer.detect_three_way_arbitrage(three_way_data)
        
        # Complex three-way arbitrage is rare but possible
        assert isinstance(opportunities, list)
        
        # If found, verify structure
        for opportunity in opportunities:
            assert len(opportunity.market_combination) == 3
            assert opportunity.correlation_risk <= analyzer.max_correlation_risk

    def test_market_correlation_matrix_calculation(self, correlation_model):
        """Test calculation of market correlation matrices"""
        
        historical_data = [
            {
                "game_id": "game1",
                "h2h_home_price": 1.75, "h2h_away_price": 2.10,
                "spread_home_price": 1.90, "spread_away_price": 1.95, "spread_line": -2.5,
                "totals_over_price": 1.85, "totals_under_price": 2.00, "totals_line": 205.5,
                "actual_home_score": 105, "actual_away_score": 98
            },
            {
                "game_id": "game2", 
                "h2h_home_price": 2.20, "h2h_away_price": 1.70,
                "spread_home_price": 2.05, "spread_away_price": 1.80, "spread_line": 3.5,
                "totals_over_price": 1.95, "totals_under_price": 1.90, "totals_line": 198.5,
                "actual_home_score": 92, "actual_away_score": 101
            }
            # More historical data would be needed for accurate correlation
        ]
        
        correlation_matrix = correlation_model.build_correlation_matrix(historical_data)
        
        # Verify correlation matrix structure
        assert isinstance(correlation_matrix, CorrelationMatrix)
        assert hasattr(correlation_matrix, 'h2h_spread_correlation')
        assert hasattr(correlation_matrix, 'h2h_totals_correlation')
        assert hasattr(correlation_matrix, 'spread_totals_correlation')
        
        # Verify correlation values are valid
        assert -1.0 <= correlation_matrix.h2h_spread_correlation <= 1.0
        assert -1.0 <= correlation_matrix.h2h_totals_correlation <= 1.0
        assert -1.0 <= correlation_matrix.spread_totals_correlation <= 1.0

    def test_arbitrage_risk_assessment(self, analyzer):
        """Test risk assessment for cross-market arbitrage opportunities"""
        
        risky_opportunity = CrossMarketOpportunity(
            game_id="risky_game",
            market_combination=["h2h", "spreads"],
            profit_margin=3.5,
            correlation_risk=0.85,  # High correlation = high risk
            selected_outcomes={"h2h": "Team A", "spreads": "Team B"},
            bookmaker_distribution={"Book1": 0.6, "Book2": 0.4}
        )
        
        risk_assessment = analyzer.assess_cross_market_risk(risky_opportunity)
        
        assert risk_assessment.overall_risk > 0.5  # High risk
        assert risk_assessment.correlation_risk == 0.85
        assert risk_assessment.recommended_stake_percentage < 0.1  # Low stake due to risk
        
        # Test low-risk opportunity
        safe_opportunity = CrossMarketOpportunity(
            game_id="safe_game",
            market_combination=["h2h", "totals"],  
            profit_margin=2.1,
            correlation_risk=0.25,  # Low correlation = lower risk
            selected_outcomes={"h2h": "Team A", "totals": "Over"},
            bookmaker_distribution={"Book1": 0.5, "Book2": 0.5}
        )
        
        safe_risk_assessment = analyzer.assess_cross_market_risk(safe_opportunity)
        
        assert safe_risk_assessment.overall_risk < 0.3  # Lower risk
        assert safe_risk_assessment.recommended_stake_percentage > 0.05

    def test_bookmaker_behavior_analysis(self, analyzer):
        """Test analysis of bookmaker behavior patterns across markets"""
        
        bookmaker_patterns = {
            "fanduel": {
                "h2h_bias": 0.02,  # Slightly favors home teams
                "spread_accuracy": 0.87,
                "totals_tendency": "over",  # Tends to set totals higher
                "market_correlation": 0.92  # High correlation between own markets
            },
            "betonlineag": {
                "h2h_bias": -0.01,  # Slightly favors away teams
                "spread_accuracy": 0.91,
                "totals_tendency": "under",
                "market_correlation": 0.88
            }
        }
        
        cross_market_data = {
            "id": "behavior_analysis_game",
            "home_team": "Team A",
            "away_team": "Team B",
            "bookmakers": [
                {
                    "key": "fanduel",
                    "title": "FanDuel",
                    "markets": [
                        {"key": "h2h", "outcomes": [
                            {"name": "Team A", "price": 1.85},
                            {"name": "Team B", "price": 1.98}
                        ]},
                        {"key": "totals", "outcomes": [
                            {"name": "Over", "price": 1.95, "point": 215.5},  # Higher total
                            {"name": "Under", "price": 1.90, "point": 215.5}
                        ]}
                    ]
                },
                {
                    "key": "betonlineag",
                    "title": "BetOnline.ag", 
                    "markets": [
                        {"key": "h2h", "outcomes": [
                            {"name": "Team A", "price": 1.90},
                            {"name": "Team B", "price": 1.93}  # Favors away slightly
                        ]},
                        {"key": "totals", "outcomes": [
                            {"name": "Over", "price": 1.88, "point": 210.5},  # Lower total
                            {"name": "Under", "price": 1.95, "point": 210.5}
                        ]}
                    ]
                }
            ]
        }
        
        with patch.object(analyzer, '_get_bookmaker_patterns', return_value=bookmaker_patterns):
            behavior_analysis = analyzer.analyze_bookmaker_behavior(cross_market_data)
            
            # Should detect bookmaker-specific patterns
            assert "fanduel" in behavior_analysis
            assert "betonlineag" in behavior_analysis
            
            # Should identify totals discrepancy (215.5 vs 210.5)
            totals_discrepancy = behavior_analysis["totals_line_difference"]
            assert abs(totals_discrepancy) == 5.0

    def test_dynamic_correlation_adjustment(self, analyzer, correlation_model):
        """Test dynamic adjustment of correlations based on game context"""
        
        # Test different game contexts
        contexts = [
            {
                "game_type": "playoff",
                "teams_rivalry": True,
                "weather": "dome",
                "time_of_season": "late"
            },
            {
                "game_type": "regular_season",
                "teams_rivalry": False, 
                "weather": "outdoor_rain",
                "time_of_season": "early"
            }
        ]
        
        base_correlation = 0.75
        
        for context in contexts:
            adjusted_correlation = correlation_model.adjust_correlation_for_context(
                base_correlation, context
            )
            
            # Correlation should be adjusted based on context
            assert adjusted_correlation != base_correlation
            assert -1.0 <= adjusted_correlation <= 1.0
            
            # Playoff games typically have higher correlation
            if context["game_type"] == "playoff":
                # May increase or decrease depending on implementation
                assert isinstance(adjusted_correlation, float)

    def test_real_time_correlation_monitoring(self, analyzer):
        """Test real-time monitoring of market correlations during games"""
        
        # Simulate live game data
        live_updates = [
            {
                "timestamp": "2025-06-09T20:00:00Z",
                "quarter": 1,
                "score": {"home": 15, "away": 12},
                "h2h_odds": {"home": 1.75, "away": 2.10},
                "spread_odds": {"home": 1.90, "away": 1.95, "line": -2.5},
                "totals_odds": {"over": 1.85, "under": 2.00, "line": 205.5}
            },
            {
                "timestamp": "2025-06-09T20:15:00Z", 
                "quarter": 1,
                "score": {"home": 28, "away": 18},  # Home team scoring run
                "h2h_odds": {"home": 1.60, "away": 2.40},  # Home becomes bigger favorite
                "spread_odds": {"home": 1.85, "away": 2.00, "line": -4.5},  # Spread increases
                "totals_odds": {"over": 1.75, "under": 2.10, "line": 210.5}  # Total increases
            }
        ]
        
        correlation_changes = analyzer.monitor_live_correlation_changes(live_updates)
        
        # Should detect correlation changes during live updates
        assert len(correlation_changes) > 0
        
        # Verify correlation change structure
        for change in correlation_changes:
            assert "timestamp" in change
            assert "correlation_delta" in change
            assert "arbitrage_impact" in change

    def test_advanced_probability_modeling(self, analyzer):
        """Test advanced probability modeling for cross-market opportunities"""
        
        market_data = {
            "h2h": {"home": 1.80, "away": 2.05},           # 55.56% + 48.78% = 104.34%
            "spreads": {"home": 1.90, "away": 1.95, "line": -2.5},  # 52.63% + 51.28% = 103.91%
            "totals": {"over": 1.85, "under": 2.00, "line": 205.5}  # 54.05% + 50.00% = 104.05%
        }
        
        # Calculate true probabilities using advanced modeling
        true_probabilities = analyzer.calculate_true_probabilities(market_data)
        
        # Should return probabilities that sum to 100% for each market
        assert abs(sum(true_probabilities["h2h"].values()) - 1.0) < 0.01
        assert abs(sum(true_probabilities["spreads"].values()) - 1.0) < 0.01
        assert abs(sum(true_probabilities["totals"].values()) - 1.0) < 0.01
        
        # Should identify most accurate probability estimates
        assert "confidence_scores" in true_probabilities
        assert all(0 <= score <= 1 for score in true_probabilities["confidence_scores"].values())

    def test_cross_market_kelly_criterion(self, analyzer):
        """Test Kelly Criterion application for cross-market betting"""
        
        opportunity = CrossMarketOpportunity(
            game_id="kelly_test_game",
            market_combination=["h2h", "spreads"],
            profit_margin=4.2,
            correlation_risk=0.30,
            selected_outcomes={"h2h": "Team A", "spreads": "Team B +3.5"},
            true_probabilities={"h2h_Team_A": 0.60, "spreads_Team_B": 0.55},
            bookmaker_odds={"h2h_Team_A": 1.80, "spreads_Team_B": 1.95}
        )
        
        kelly_stakes = analyzer.calculate_kelly_stakes(opportunity, bankroll=10000)
        
        # Kelly criterion should recommend optimal stake sizes
        assert "h2h_stake" in kelly_stakes
        assert "spreads_stake" in kelly_stakes
        
        # Stakes should be reasonable percentages of bankroll
        total_stake = kelly_stakes["h2h_stake"] + kelly_stakes["spreads_stake"]
        assert 0 < total_stake < 5000  # Should not risk more than 50% of bankroll
        
        # Should include risk adjustment for correlation
        assert kelly_stakes["risk_adjustment_factor"] < 1.0