"""
WNBA Arbitrage AI Tool - Multi-Source Data Ingestion
Advanced data collection from multiple sources with scraping capabilities
"""

import asyncio
import aiohttp
import requests
import time
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import redis
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import random
from dotenv import load_dotenv
import os

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OddsData:
    """Standardized odds data structure"""
    game_id: str
    home_team: str
    away_team: str
    commence_time: str
    bookmaker: str
    market_type: str  # 'h2h', 'spreads', 'totals'
    outcomes: List[Dict[str, Union[str, float]]]
    last_update: str
    source: str

@dataclass
class ArbitrageOpportunity:
    """Detected arbitrage opportunity"""
    game_id: str
    game_description: str
    market_type: str
    profit_margin: float
    profit_percentage: float
    best_odds: Dict[str, Dict]
    total_stake: float
    individual_stakes: Dict[str, float]
    detected_at: str
    expiry_estimate: str

class RateLimitManager:
    """Manages rate limiting across all data sources"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis.Redis() if redis_client is None else redis_client
        self.limits = {
            'odds_api': {'requests_per_minute': 60, 'requests_per_day': 500},
            'bovada_scraper': {'requests_per_minute': 0.5, 'requests_per_day': 720},
            'betonline_scraper': {'requests_per_minute': 1, 'requests_per_day': 1440},
            'mybookie_scraper': {'requests_per_minute': 0.75, 'requests_per_day': 1080},
        }
    
    def can_make_request(self, source: str) -> bool:
        """Check if request can be made within rate limits"""
        now = datetime.now()
        minute_key = f"rate_limit:{source}:minute:{now.strftime('%Y%m%d%H%M')}"
        day_key = f"rate_limit:{source}:day:{now.strftime('%Y%m%d')}"
        
        try:
            minute_count = int(self.redis_client.get(minute_key) or 0)
            day_count = int(self.redis_client.get(day_key) or 0)
            
            limits = self.limits.get(source, {'requests_per_minute': 1, 'requests_per_day': 100})
            
            if minute_count >= limits['requests_per_minute']:
                return False
            if day_count >= limits['requests_per_day']:
                return False
                
            return True
        except Exception as e:
            logger.warning(f"Rate limit check failed for {source}: {e}")
            return True  # Allow request if Redis is down
    
    def record_request(self, source: str):
        """Record a request for rate limiting"""
        now = datetime.now()
        minute_key = f"rate_limit:{source}:minute:{now.strftime('%Y%m%d%H%M')}"
        day_key = f"rate_limit:{source}:day:{now.strftime('%Y%m%d')}"
        
        try:
            pipe = self.redis_client.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)
            pipe.incr(day_key)
            pipe.expire(day_key, 86400)
            pipe.execute()
        except Exception as e:
            logger.warning(f"Failed to record request for {source}: {e}")

class BaseDataSource(ABC):
    """Abstract base class for all data sources"""
    
    def __init__(self, rate_limiter: RateLimitManager):
        self.rate_limiter = rate_limiter
        self.source_name = self.__class__.__name__.lower()
        
    @abstractmethod
    async def get_wnba_odds(self) -> List[OddsData]:
        """Get WNBA odds from this source"""
        pass
    
    @abstractmethod
    def get_source_health(self) -> Dict[str, Any]:
        """Get health status of this source"""
        pass

class EnhancedOddsAPI(BaseDataSource):
    """Enhanced version of The Odds API integration"""
    
    def __init__(self, rate_limiter: RateLimitManager, api_key: str = None):
        super().__init__(rate_limiter)
        self.api_key = api_key or os.getenv('ODDS_API_KEY')
        self.base_url = 'https://api.the-odds-api.com/v4'
        self.sport_key = 'basketball_wnba'
        
    async def get_wnba_odds(self) -> List[OddsData]:
        """Get WNBA odds from The Odds API"""
        if not self.rate_limiter.can_make_request('odds_api'):
            logger.warning("Rate limit exceeded for The Odds API")
            return []
            
        url = f"{self.base_url}/sports/{self.sport_key}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': 'us,us2,uk',  # Include offshore books
            'markets': 'h2h,spreads,totals',
            'oddsFormat': 'american',
            'dateFormat': 'iso'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.rate_limiter.record_request('odds_api')
                        return self._parse_odds_api_response(data)
                    else:
                        logger.error(f"The Odds API request failed: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"The Odds API error: {e}")
            return []
    
    def _parse_odds_api_response(self, data: List[Dict]) -> List[OddsData]:
        """Parse The Odds API response into standardized format"""
        odds_list = []
        
        for game in data:
            for bookmaker in game.get('bookmakers', []):
                for market in bookmaker.get('markets', []):
                    odds_data = OddsData(
                        game_id=game['id'],
                        home_team=game['home_team'],
                        away_team=game['away_team'],
                        commence_time=game['commence_time'],
                        bookmaker=bookmaker['key'],
                        market_type=market['key'],
                        outcomes=market['outcomes'],
                        last_update=market['last_update'],
                        source='odds_api'
                    )
                    odds_list.append(odds_data)
        
        return odds_list
    
    def get_source_health(self) -> Dict[str, Any]:
        """Get health status of The Odds API"""
        return {
            'source': 'odds_api',
            'status': 'healthy' if self.api_key else 'no_api_key',
            'rate_limit_status': 'ok' if self.rate_limiter.can_make_request('odds_api') else 'limited'
        }

class BovadaScraper(BaseDataSource):
    """Bovada odds scraper with anti-detection measures"""
    
    def __init__(self, rate_limiter: RateLimitManager):
        super().__init__(rate_limiter)
        self.base_url = "https://www.bovada.lv"
        self.wnba_endpoint = "/services/sports/event/coupon/events/A/description/basketball/wnba"
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
    
    async def get_wnba_odds(self) -> List[OddsData]:
        """Get WNBA odds from Bovada"""
        if not self.rate_limiter.can_make_request('bovada_scraper'):
            logger.warning("Rate limit exceeded for Bovada scraper")
            return []
        
        # Add random delay for natural behavior
        await asyncio.sleep(random.uniform(2, 5))
        
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.bovada.lv/sports/basketball/wnba',
            'Cache-Control': 'no-cache',
        }
        
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                url = f"{self.base_url}{self.wnba_endpoint}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.rate_limiter.record_request('bovada_scraper')
                        return self._parse_bovada_response(data)
                    else:
                        logger.error(f"Bovada request failed: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Bovada scraping error: {e}")
            return []
    
    def _parse_bovada_response(self, data: Dict) -> List[OddsData]:
        """Parse Bovada response into standardized format"""
        odds_list = []
        
        try:
            events = data.get('events', [])
            for event in events:
                # Extract game information
                game_id = f"bovada_{event.get('id')}"
                competitors = event.get('competitors', [])
                if len(competitors) >= 2:
                    home_team = competitors[0].get('name')
                    away_team = competitors[1].get('name')
                    
                    # Extract odds from different markets
                    for market in event.get('displayGroups', []):
                        market_type = self._map_bovada_market(market.get('description', ''))
                        if market_type:
                            outcomes = []
                            for outcome in market.get('markets', []):
                                for selection in outcome.get('outcomes', []):
                                    outcomes.append({
                                        'name': selection.get('description'),
                                        'price': selection.get('price', {}).get('american'),
                                        'point': selection.get('price', {}).get('handicap')
                                    })
                            
                            odds_data = OddsData(
                                game_id=game_id,
                                home_team=home_team,
                                away_team=away_team,
                                commence_time=event.get('startTime'),
                                bookmaker='bovada',
                                market_type=market_type,
                                outcomes=outcomes,
                                last_update=datetime.now(timezone.utc).isoformat(),
                                source='bovada_scraper'
                            )
                            odds_list.append(odds_data)
        except Exception as e:
            logger.error(f"Error parsing Bovada response: {e}")
        
        return odds_list
    
    def _map_bovada_market(self, description: str) -> Optional[str]:
        """Map Bovada market descriptions to standard format"""
        description_lower = description.lower()
        if 'moneyline' in description_lower or 'match result' in description_lower:
            return 'h2h'
        elif 'spread' in description_lower or 'handicap' in description_lower:
            return 'spreads'
        elif 'total' in description_lower or 'over/under' in description_lower:
            return 'totals'
        return None
    
    def get_source_health(self) -> Dict[str, Any]:
        """Get health status of Bovada scraper"""
        return {
            'source': 'bovada_scraper',
            'status': 'operational',
            'rate_limit_status': 'ok' if self.rate_limiter.can_make_request('bovada_scraper') else 'limited',
            'anti_detection': 'active'
        }

class BetOnlineScraper(BaseDataSource):
    """BetOnline odds scraper using Selenium"""
    
    def __init__(self, rate_limiter: RateLimitManager):
        super().__init__(rate_limiter)
        self.base_url = "https://www.betonline.ag"
        self.wnba_url = "/sportsbook/basketball/wnba"
    
    def _create_driver(self):
        """Create Selenium WebDriver with anti-detection settings"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        return webdriver.Chrome(options=options)
    
    async def get_wnba_odds(self) -> List[OddsData]:
        """Get WNBA odds from BetOnline"""
        if not self.rate_limiter.can_make_request('betonline_scraper'):
            logger.warning("Rate limit exceeded for BetOnline scraper")
            return []
        
        driver = None
        try:
            driver = self._create_driver()
            driver.get(f"{self.base_url}{self.wnba_url}")
            
            # Wait for page to load
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "event-row")))
            
            # Add random delay
            await asyncio.sleep(random.uniform(3, 7))
            
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            self.rate_limiter.record_request('betonline_scraper')
            return self._parse_betonline_html(soup)
            
        except Exception as e:
            logger.error(f"BetOnline scraping error: {e}")
            return []
        finally:
            if driver:
                driver.quit()
    
    def _parse_betonline_html(self, soup: BeautifulSoup) -> List[OddsData]:
        """Parse BetOnline HTML into standardized format"""
        odds_list = []
        
        try:
            # Find WNBA game rows
            game_rows = soup.find_all('div', class_='event-row')
            
            for row in game_rows:
                # Extract team names
                teams = row.find_all('span', class_='team-name')
                if len(teams) >= 2:
                    away_team = teams[0].text.strip()
                    home_team = teams[1].text.strip()
                    
                    # Extract odds
                    odds_cells = row.find_all('span', class_='odds')
                    if len(odds_cells) >= 2:
                        game_id = f"betonline_{hash(f'{home_team}_{away_team}')}"
                        
                        outcomes = [
                            {'name': away_team, 'price': self._parse_american_odds(odds_cells[0].text)},
                            {'name': home_team, 'price': self._parse_american_odds(odds_cells[1].text)}
                        ]
                        
                        odds_data = OddsData(
                            game_id=game_id,
                            home_team=home_team,
                            away_team=away_team,
                            commence_time=datetime.now(timezone.utc).isoformat(),  # BetOnline doesn't provide exact times easily
                            bookmaker='betonline',
                            market_type='h2h',
                            outcomes=outcomes,
                            last_update=datetime.now(timezone.utc).isoformat(),
                            source='betonline_scraper'
                        )
                        odds_list.append(odds_data)
        
        except Exception as e:
            logger.error(f"Error parsing BetOnline HTML: {e}")
        
        return odds_list
    
    def _parse_american_odds(self, odds_text: str) -> Optional[int]:
        """Parse American odds from text"""
        try:
            odds_text = odds_text.strip().replace('+', '')
            return int(odds_text) if odds_text.isdigit() or (odds_text.startswith('-') and odds_text[1:].isdigit()) else None
        except:
            return None
    
    def get_source_health(self) -> Dict[str, Any]:
        """Get health status of BetOnline scraper"""
        return {
            'source': 'betonline_scraper',
            'status': 'operational',
            'rate_limit_status': 'ok' if self.rate_limiter.can_make_request('betonline_scraper') else 'limited',
            'method': 'selenium'
        }

class MultiSourceDataAggregator:
    """Aggregates data from multiple sources and detects arbitrage opportunities"""
    
    def __init__(self):
        self.rate_limiter = RateLimitManager()
        self.redis_client = redis.Redis()
        self.sources = self._initialize_sources()
        
    def _initialize_sources(self) -> List[BaseDataSource]:
        """Initialize all data sources"""
        sources = []
        
        # Add The Odds API if key is available
        if os.getenv('ODDS_API_KEY'):
            sources.append(EnhancedOddsAPI(self.rate_limiter))
        
        # Add scrapers
        sources.append(BovadaScraper(self.rate_limiter))
        sources.append(BetOnlineScraper(self.rate_limiter))
        
        return sources
    
    async def collect_all_odds(self) -> Dict[str, List[OddsData]]:
        """Collect odds from all available sources"""
        results = {}
        
        # Run all sources concurrently
        tasks = []
        for source in self.sources:
            task = asyncio.create_task(source.get_wnba_odds())
            tasks.append((source.__class__.__name__, task))
        
        for source_name, task in tasks:
            try:
                odds_data = await task
                results[source_name.lower()] = odds_data
                logger.info(f"Collected {len(odds_data)} odds from {source_name}")
            except Exception as e:
                logger.error(f"Failed to collect from {source_name}: {e}")
                results[source_name.lower()] = []
        
        # Cache results
        self._cache_odds_data(results)
        
        return results
    
    def _cache_odds_data(self, odds_data: Dict[str, List[OddsData]]):
        """Cache odds data in Redis"""
        try:
            cache_key = f"odds_data:{datetime.now().strftime('%Y%m%d%H%M')}"
            serialized_data = json.dumps(odds_data, default=self._serialize_odds_data)
            self.redis_client.setex(cache_key, 300, serialized_data)  # Cache for 5 minutes
        except Exception as e:
            logger.warning(f"Failed to cache odds data: {e}")
    
    def _serialize_odds_data(self, obj):
        """Custom serializer for OddsData objects"""
        if isinstance(obj, OddsData):
            return obj.__dict__
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def detect_arbitrage_opportunities(self, odds_data: Dict[str, List[OddsData]], 
                                     min_profit_margin: float = 0.02) -> List[ArbitrageOpportunity]:
        """Detect arbitrage opportunities across all sources"""
        opportunities = []
        
        # Group odds by game and market
        game_markets = {}
        for source, odds_list in odds_data.items():
            for odds in odds_list:
                key = f"{odds.home_team}_{odds.away_team}_{odds.market_type}"
                if key not in game_markets:
                    game_markets[key] = []
                game_markets[key].append(odds)
        
        # Check each game market for arbitrage
        for game_key, odds_list in game_markets.items():
            if len(odds_list) < 2:  # Need at least 2 sources
                continue
                
            arb_opp = self._calculate_arbitrage(odds_list, min_profit_margin)
            if arb_opp:
                opportunities.append(arb_opp)
        
        return opportunities
    
    def _calculate_arbitrage(self, odds_list: List[OddsData], 
                           min_profit_margin: float) -> Optional[ArbitrageOpportunity]:
        """Calculate arbitrage opportunity for a specific game market"""
        if not odds_list:
            return None
        
        # Find best odds for each outcome
        best_odds = {}
        
        for odds in odds_list:
            for outcome in odds.outcomes:
                outcome_name = outcome.get('name')
                price = outcome.get('price')
                
                if outcome_name and price:
                    if outcome_name not in best_odds or abs(price) > abs(best_odds[outcome_name]['price']):
                        best_odds[outcome_name] = {
                            'price': price,
                            'bookmaker': odds.bookmaker,
                            'source': odds.source
                        }
        
        if len(best_odds) < 2:
            return None
        
        # Calculate implied probabilities
        total_implied_prob = 0
        for outcome_data in best_odds.values():
            price = outcome_data['price']
            if price > 0:
                implied_prob = 100 / (price + 100)
            else:
                implied_prob = abs(price) / (abs(price) + 100)
            total_implied_prob += implied_prob
        
        profit_margin = 1 - total_implied_prob
        
        if profit_margin > min_profit_margin:
            # Calculate optimal stakes
            total_stake = 1000  # $1000 example
            individual_stakes = {}
            
            for outcome, data in best_odds.items():
                price = data['price']
                if price > 0:
                    implied_prob = 100 / (price + 100)
                else:
                    implied_prob = abs(price) / (abs(price) + 100)
                
                stake = (implied_prob / total_implied_prob) * total_stake
                individual_stakes[outcome] = round(stake, 2)
            
            return ArbitrageOpportunity(
                game_id=odds_list[0].game_id,
                game_description=f"{odds_list[0].away_team} @ {odds_list[0].home_team}",
                market_type=odds_list[0].market_type,
                profit_margin=profit_margin,
                profit_percentage=profit_margin * 100,
                best_odds=best_odds,
                total_stake=total_stake,
                individual_stakes=individual_stakes,
                detected_at=datetime.now(timezone.utc).isoformat(),
                expiry_estimate=(datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
            )
        
        return None
    
    async def get_real_time_opportunities(self, min_profit: float = 0.02) -> List[ArbitrageOpportunity]:
        """Get real-time arbitrage opportunities"""
        odds_data = await self.collect_all_odds()
        opportunities = self.detect_arbitrage_opportunities(odds_data, min_profit)
        
        # Log opportunities
        if opportunities:
            logger.info(f"Found {len(opportunities)} arbitrage opportunities")
            for opp in opportunities:
                logger.info(f"Arbitrage: {opp.game_description} - {opp.profit_percentage:.2f}% profit")
        
        return opportunities
    
    def get_all_source_health(self) -> Dict[str, Any]:
        """Get health status of all sources"""
        health_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'sources': {}
        }
        
        for source in self.sources:
            try:
                health_data['sources'][source.__class__.__name__.lower()] = source.get_source_health()
            except Exception as e:
                health_data['sources'][source.__class__.__name__.lower()] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return health_data

# Main interface functions
async def get_multi_source_odds() -> Dict[str, List[OddsData]]:
    """Get odds from all sources"""
    aggregator = MultiSourceDataAggregator()
    return await aggregator.collect_all_odds()

async def find_real_time_arbitrage(min_profit: float = 0.02) -> List[ArbitrageOpportunity]:
    """Find real-time arbitrage opportunities"""
    aggregator = MultiSourceDataAggregator()
    return await aggregator.get_real_time_opportunities(min_profit)

def get_source_health() -> Dict[str, Any]:
    """Get health status of all sources"""
    aggregator = MultiSourceDataAggregator()
    return aggregator.get_all_source_health()

if __name__ == "__main__":
    # Test the multi-source system
    async def main():
        print("Testing Multi-Source Data Ingestion...")
        
        # Test source health
        health = get_source_health()
        print(f"Source Health: {json.dumps(health, indent=2)}")
        
        # Test odds collection
        odds_data = await get_multi_source_odds()
        print(f"Collected odds from {len(odds_data)} sources")
        
        # Test arbitrage detection
        opportunities = await find_real_time_arbitrage(0.01)
        print(f"Found {len(opportunities)} arbitrage opportunities")
        
        if opportunities:
            print(f"Best opportunity: {opportunities[0].profit_percentage:.2f}% profit")
    
    asyncio.run(main())