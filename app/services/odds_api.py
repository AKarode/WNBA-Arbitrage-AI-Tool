"""
WNBA Arbitrage AI Tool - Odds API Service
Comprehensive service for fetching odds data from multiple sources
"""

import os
import requests
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


class OddsAPIError(Exception):
    """Custom exception for odds API errors"""
    pass


class BaseOddsProvider:
    """Base class for odds providers"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url
        self.rate_limit_delay = 1.0  # Default delay between requests
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: Dict = None, headers: Dict = None) -> Dict:
        """Make HTTP request with error handling"""
        self._rate_limit()
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise OddsAPIError(f"Request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise OddsAPIError(f"Invalid JSON response: {str(e)}")


class TheOddsAPI(BaseOddsProvider):
    """The Odds API provider - primary source for WNBA odds"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ODDS_API_KEY')
        self.base_url = os.getenv('ODDS_API_BASE_URL', 'https://api.the-odds-api.com/v4')
        super().__init__(self.api_key, self.base_url)
        
        if not self.api_key:
            raise OddsAPIError("The Odds API key not found. Please set ODDS_API_KEY environment variable.")
        
        # The Odds API specific settings
        self.rate_limit_delay = 60.0  # Free tier: 500 requests per month, so be conservative
        self.sport_key = 'basketball_wnba'
        self.regions = ['us', 'us2']  # US regions for offshore books
        self.markets = ['h2h', 'spreads', 'totals']  # Main betting markets
        self.odds_format = 'american'
        
    def get_wnba_odds(self, bookmakers: List[str] = None, include_live: bool = True) -> Dict:
        """
        Get current WNBA odds from The Odds API
        
        Args:
            bookmakers: List of specific bookmakers to include (optional)
            include_live: Whether to include live/in-play odds
            
        Returns:
            Dict containing odds data with metadata
        """
        url = f"{self.base_url}/sports/{self.sport_key}/odds"
        
        params = {
            'apiKey': self.api_key,
            'regions': ','.join(self.regions),
            'markets': ','.join(self.markets),
            'oddsFormat': self.odds_format,
            'dateFormat': 'iso'
        }
        
        if bookmakers:
            params['bookmakers'] = ','.join(bookmakers)
            
        try:
            data = self._make_request(url, params)
            
            # Add metadata
            result = {
                'source': 'the_odds_api',
                'sport': self.sport_key,
                'retrieved_at': datetime.now(timezone.utc).isoformat(),
                'markets': self.markets,
                'regions': self.regions,
                'total_games': len(data) if isinstance(data, list) else 0,
                'data': data
            }
            
            return result
            
        except Exception as e:
            raise OddsAPIError(f"Failed to fetch WNBA odds: {str(e)}")
    
    def get_bookmakers(self) -> List[Dict]:
        """Get list of available bookmakers"""
        url = f"{self.base_url}/sports/{self.sport_key}/odds"
        
        params = {
            'apiKey': self.api_key,
            'regions': ','.join(self.regions),
            'markets': 'h2h',  # Just get one market to see bookmakers
            'oddsFormat': self.odds_format
        }
        
        try:
            data = self._make_request(url, params)
            bookmakers = set()
            
            if isinstance(data, list):
                for game in data:
                    if 'bookmakers' in game:
                        for book in game['bookmakers']:
                            bookmakers.add(book.get('key'))
            
            return sorted(list(bookmakers))
            
        except Exception as e:
            raise OddsAPIError(f"Failed to fetch bookmakers: {str(e)}")
    
    def get_usage_info(self) -> Dict:
        """Get API usage information (requests remaining)"""
        # The Odds API doesn't have a specific endpoint for this,
        # but we can check headers from the last response
        # For now, return a placeholder
        return {
            'provider': 'the_odds_api',
            'plan': 'free_tier',
            'requests_remaining': 'unknown',
            'requests_used': 'unknown',
            'reset_time': 'monthly'
        }


class OffshoreBookScraper:
    """
    Scraper for offshore sportsbooks that don't have public APIs
    Note: This is a placeholder for future implementation
    Many offshore books require custom scraping solutions
    """
    
    def __init__(self):
        self.supported_books = [
            'bovada',
            'mybookie',
            'betonline',
            'heritage',
            'gtbets',
            'xbet'
        ]
    
    def get_bovada_odds(self) -> Dict:
        """Placeholder for Bovada scraping"""
        # This would require custom scraping implementation
        # Bovada typically uses dynamic content that requires specialized handling
        return {
            'source': 'bovada',
            'status': 'not_implemented',
            'message': 'Bovada scraping requires custom implementation'
        }
    
    def get_mybookie_odds(self) -> Dict:
        """Placeholder for MyBookie scraping"""
        return {
            'source': 'mybookie',
            'status': 'not_implemented',
            'message': 'MyBookie scraping requires custom implementation'
        }


class OddsAggregator:
    """Main service class that aggregates odds from multiple sources"""
    
    def __init__(self):
        self.providers = {}
        self.initialize_providers()
    
    def initialize_providers(self):
        """Initialize all available odds providers"""
        try:
            # Initialize The Odds API if key is available
            if os.getenv('ODDS_API_KEY'):
                self.providers['the_odds_api'] = TheOddsAPI()
            
            # Initialize offshore scraper (placeholder)
            self.providers['offshore_scraper'] = OffshoreBookScraper()
            
        except Exception as e:
            print(f"Warning: Failed to initialize some providers: {str(e)}")
    
    def get_all_wnba_odds(self) -> Dict:
        """Get WNBA odds from all available sources"""
        results = {
            'aggregated_at': datetime.now(timezone.utc).isoformat(),
            'sources': {},
            'errors': [],
            'summary': {
                'total_sources': 0,
                'successful_sources': 0,
                'total_games': 0,
                'total_bookmakers': set()
            }
        }
        
        for provider_name, provider in self.providers.items():
            try:
                if provider_name == 'the_odds_api' and hasattr(provider, 'get_wnba_odds'):
                    odds_data = provider.get_wnba_odds()
                    results['sources'][provider_name] = odds_data
                    results['summary']['successful_sources'] += 1
                    results['summary']['total_games'] += odds_data.get('total_games', 0)
                    
                    # Extract bookmaker names
                    if 'data' in odds_data and isinstance(odds_data['data'], list):
                        for game in odds_data['data']:
                            if 'bookmakers' in game:
                                for book in game['bookmakers']:
                                    results['summary']['total_bookmakers'].add(book.get('key'))
                
                results['summary']['total_sources'] += 1
                
            except Exception as e:
                error_msg = f"Error fetching from {provider_name}: {str(e)}"
                results['errors'].append(error_msg)
                print(f"Warning: {error_msg}")
        
        # Convert set to list for JSON serialization
        results['summary']['total_bookmakers'] = list(results['summary']['total_bookmakers'])
        
        return results
    
    def find_arbitrage_opportunities(self, odds_data: Dict, min_profit_margin: float = 0.01) -> List[Dict]:
        """
        Analyze odds data to find arbitrage opportunities
        
        Args:
            odds_data: Aggregated odds data from get_all_wnba_odds()
            min_profit_margin: Minimum profit margin to consider (1% = 0.01)
            
        Returns:
            List of arbitrage opportunities found
        """
        opportunities = []
        
        # Extract odds from The Odds API data
        if 'the_odds_api' in odds_data.get('sources', {}):
            api_data = odds_data['sources']['the_odds_api'].get('data', [])
            
            for game in api_data:
                if not game.get('bookmakers'):
                    continue
                
                # Analyze each market (h2h, spreads, totals)
                for market_type in ['h2h', 'spreads', 'totals']:
                    arb_opp = self._find_market_arbitrage(game, market_type, min_profit_margin)
                    if arb_opp:
                        opportunities.append(arb_opp)
        
        return opportunities
    
    def _find_market_arbitrage(self, game: Dict, market_type: str, min_profit_margin: float) -> Optional[Dict]:
        """Find arbitrage opportunity in a specific market"""
        best_odds = {}
        
        # Extract best odds for each outcome
        for bookmaker in game.get('bookmakers', []):
            for market in bookmaker.get('markets', []):
                if market.get('key') != market_type:
                    continue
                
                for outcome in market.get('outcomes', []):
                    outcome_key = outcome.get('name')
                    if market_type in ['spreads', 'totals']:
                        # Include point spread/total in the key
                        point = outcome.get('point', 0)
                        outcome_key = f"{outcome_key}_{point}"
                    
                    price = outcome.get('price')
                    if price and outcome_key:
                        if outcome_key not in best_odds or abs(price) > abs(best_odds[outcome_key]['price']):
                            best_odds[outcome_key] = {
                                'price': price,
                                'bookmaker': bookmaker.get('key'),
                                'last_update': market.get('last_update')
                            }
        
        # Check for arbitrage opportunity
        if len(best_odds) >= 2:
            # Convert American odds to implied probabilities
            implied_probs = []
            for outcome_data in best_odds.values():
                price = outcome_data['price']
                if price > 0:
                    implied_prob = 100 / (price + 100)
                else:
                    implied_prob = abs(price) / (abs(price) + 100)
                implied_probs.append(implied_prob)
            
            total_implied_prob = sum(implied_probs)
            profit_margin = (1 - total_implied_prob)
            
            if profit_margin > min_profit_margin:
                return {
                    'game_id': game.get('id'),
                    'game': f"{game.get('away_team')} @ {game.get('home_team')}",
                    'commence_time': game.get('commence_time'),
                    'market_type': market_type,
                    'profit_margin': profit_margin,
                    'profit_percentage': profit_margin * 100,
                    'best_odds': best_odds,
                    'total_implied_probability': total_implied_prob,
                    'detected_at': datetime.now(timezone.utc).isoformat()
                }
        
        return None
    
    def get_provider_status(self) -> Dict:
        """Get status of all odds providers"""
        status = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'providers': {}
        }
        
        for provider_name, provider in self.providers.items():
            try:
                if provider_name == 'the_odds_api' and hasattr(provider, 'get_usage_info'):
                    status['providers'][provider_name] = provider.get_usage_info()
                else:
                    status['providers'][provider_name] = {
                        'status': 'available',
                        'type': 'scraper' if 'scraper' in provider_name else 'api'
                    }
            except Exception as e:
                status['providers'][provider_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return status


# Main interface functions
def get_wnba_odds() -> Dict:
    """Get current WNBA odds from all sources"""
    aggregator = OddsAggregator()
    return aggregator.get_all_wnba_odds()


def find_arbitrage_opportunities(min_profit: float = 0.01) -> List[Dict]:
    """Find current arbitrage opportunities"""
    aggregator = OddsAggregator()
    odds_data = aggregator.get_all_wnba_odds()
    return aggregator.find_arbitrage_opportunities(odds_data, min_profit)


def get_provider_status() -> Dict:
    """Get status of all odds providers"""
    aggregator = OddsAggregator()
    return aggregator.get_provider_status()


if __name__ == "__main__":
    # Test the service
    print("Testing WNBA Odds API Service...")
    
    try:
        # Test provider status
        status = get_provider_status()
        print(f"Provider Status: {json.dumps(status, indent=2)}")
        
        # Test odds fetching (only if API key is available)
        if os.getenv('ODDS_API_KEY'):
            print("\nFetching WNBA odds...")
            odds = get_wnba_odds()
            print(f"Odds Summary: {json.dumps(odds['summary'], indent=2)}")
            
            # Test arbitrage detection
            print("\nLooking for arbitrage opportunities...")
            arb_opps = find_arbitrage_opportunities(0.01)
            print(f"Found {len(arb_opps)} arbitrage opportunities")
            
            if arb_opps:
                print(f"Best opportunity: {arb_opps[0]['profit_percentage']:.2f}% profit")
        else:
            print("No API key found. Set ODDS_API_KEY to test live data fetching.")
            
    except Exception as e:
        print(f"Error during testing: {str(e)}") 