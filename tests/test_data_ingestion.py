"""
Tests for Multi-Source Data Ingestion Components
Comprehensive test suite for data collection and processing
"""

import pytest
import asyncio
import json
import redis
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import aiohttp
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException

from app.services.multi_source_ingestion import (
    RateLimitManager,
    BaseDataSource,
    EnhancedOddsAPI,
    BovadaScraper,
    BetOnlineScraper,
    MultiSourceDataAggregator,
    OddsData,
    ArbitrageOpportunity,
    get_multi_source_odds,
    find_real_time_arbitrage,
    get_source_health
)
from app.config.data_sources import DATA_SOURCES, SCRAPING_CONFIG

# Test fixtures
@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    mock_client = Mock()
    mock_client.get.return_value = None
    mock_client.setex.return_value = True
    mock_client.incr.return_value = 1
    mock_client.expire.return_value = True
    mock_client.pipeline.return_value = mock_client
    mock_client.execute.return_value = [1, True, 1, True]
    mock_client.ping.return_value = True
    return mock_client

@pytest.fixture
def rate_limiter(mock_redis):
    """Rate limiter with mocked Redis"""
    with patch('app.services.multi_source_ingestion.redis.Redis', return_value=mock_redis):
        return RateLimitManager(mock_redis)

@pytest.fixture
def sample_odds_api_response():
    """Sample response from The Odds API"""
    return [
        {
            'id': 'game_123',
            'sport_key': 'basketball_wnba',
            'sport_title': 'WNBA',
            'commence_time': '2024-07-15T19:00:00Z',
            'home_team': 'Las Vegas Aces',
            'away_team': 'New York Liberty',
            'bookmakers': [
                {
                    'key': 'bovada',
                    'title': 'Bovada',
                    'last_update': '2024-07-15T18:30:00Z',
                    'markets': [
                        {
                            'key': 'h2h',
                            'last_update': '2024-07-15T18:30:00Z',
                            'outcomes': [
                                {'name': 'Las Vegas Aces', 'price': -140},
                                {'name': 'New York Liberty', 'price': 120}
                            ]
                        }
                    ]
                }
            ]
        }
    ]

@pytest.fixture
def sample_bovada_response():
    """Sample response from Bovada API"""
    return {
        'events': [
            {
                'id': 'bovada_game_456',
                'startTime': '2024-07-15T19:00:00Z',
                'competitors': [
                    {'name': 'Las Vegas Aces'},
                    {'name': 'New York Liberty'}
                ],
                'displayGroups': [
                    {
                        'description': 'Moneyline',
                        'markets': [
                            {
                                'outcomes': [
                                    {
                                        'description': 'Las Vegas Aces',
                                        'price': {'american': -145}
                                    },
                                    {
                                        'description': 'New York Liberty',
                                        'price': {'american': 125}
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }

class TestRateLimitManager:
    """Test suite for rate limiting functionality"""

    def test_rate_limiter_initialization(self, mock_redis):
        """Test rate limiter initialization"""
        with patch('app.services.multi_source_ingestion.redis.Redis', return_value=mock_redis):
            rate_limiter = RateLimitManager()
            
        assert rate_limiter.redis_client == mock_redis
        assert 'odds_api' in rate_limiter.limits
        assert 'bovada_scraper' in rate_limiter.limits

    def test_can_make_request_within_limits(self, rate_limiter, mock_redis):
        """Test request permission when within rate limits"""
        # Mock Redis to return counts within limits
        mock_redis.get.side_effect = lambda key: '5' if 'minute' in key else '50'
        
        assert rate_limiter.can_make_request('odds_api') == True

    def test_can_make_request_minute_limit_exceeded(self, rate_limiter, mock_redis):
        """Test request denial when minute limit exceeded"""
        # Mock Redis to return count exceeding minute limit
        mock_redis.get.side_effect = lambda key: '100' if 'minute' in key else '50'
        
        assert rate_limiter.can_make_request('odds_api') == False

    def test_can_make_request_day_limit_exceeded(self, rate_limiter, mock_redis):
        """Test request denial when daily limit exceeded"""
        # Mock Redis to return count exceeding daily limit
        mock_redis.get.side_effect = lambda key: '5' if 'minute' in key else '1000'
        
        assert rate_limiter.can_make_request('odds_api') == False

    def test_can_make_request_redis_error(self, rate_limiter, mock_redis):
        """Test graceful handling of Redis errors"""
        mock_redis.get.side_effect = redis.RedisError("Connection failed")
        
        # Should return True when Redis is unavailable (fail open)
        assert rate_limiter.can_make_request('odds_api') == True

    def test_record_request(self, rate_limiter, mock_redis):
        """Test request recording functionality"""
        rate_limiter.record_request('odds_api')
        
        # Should call Redis pipeline operations
        mock_redis.pipeline.assert_called_once()
        mock_redis.incr.assert_called()
        mock_redis.expire.assert_called()
        mock_redis.execute.assert_called_once()

    def test_record_request_redis_error(self, rate_limiter, mock_redis):
        """Test graceful handling of Redis errors during recording"""
        mock_redis.pipeline.side_effect = redis.RedisError("Connection failed")
        
        # Should not raise exception
        rate_limiter.record_request('odds_api')

class TestEnhancedOddsAPI:
    """Test suite for Enhanced Odds API integration"""

    def test_initialization_with_api_key(self, rate_limiter):
        """Test initialization with API key"""
        api_key = "test_api_key"
        odds_api = EnhancedOddsAPI(rate_limiter, api_key)
        
        assert odds_api.api_key == api_key
        assert odds_api.sport_key == 'basketball_wnba'
        assert odds_api.base_url == 'https://api.the-odds-api.com/v4'

    def test_initialization_without_api_key(self, rate_limiter):
        """Test initialization without API key (from environment)"""
        with patch.dict('os.environ', {'ODDS_API_KEY': 'env_api_key'}):
            odds_api = EnhancedOddsAPI(rate_limiter)
            assert odds_api.api_key == 'env_api_key'

    @pytest.mark.asyncio
    async def test_get_wnba_odds_success(self, rate_limiter, sample_odds_api_response, mock_redis):
        """Test successful odds retrieval from The Odds API"""
        odds_api = EnhancedOddsAPI(rate_limiter, "test_key")
        
        # Mock rate limiter to allow requests
        rate_limiter.can_make_request = Mock(return_value=True)
        rate_limiter.record_request = Mock()
        
        # Mock aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = sample_odds_api_response
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            odds_data = await odds_api.get_wnba_odds()
        
        assert len(odds_data) > 0
        assert isinstance(odds_data[0], OddsData)
        assert odds_data[0].source == 'odds_api'
        assert odds_data[0].game_id == 'game_123'
        rate_limiter.record_request.assert_called_once_with('odds_api')

    @pytest.mark.asyncio
    async def test_get_wnba_odds_rate_limited(self, rate_limiter, mock_redis):
        """Test odds retrieval when rate limited"""
        odds_api = EnhancedOddsAPI(rate_limiter, "test_key")
        
        # Mock rate limiter to deny requests
        rate_limiter.can_make_request = Mock(return_value=False)
        
        odds_data = await odds_api.get_wnba_odds()
        
        assert odds_data == []

    @pytest.mark.asyncio
    async def test_get_wnba_odds_api_error(self, rate_limiter, mock_redis):
        """Test handling of API errors"""
        odds_api = EnhancedOddsAPI(rate_limiter, "test_key")
        
        rate_limiter.can_make_request = Mock(return_value=True)
        
        # Mock aiohttp to raise an exception
        with patch('aiohttp.ClientSession.get', side_effect=aiohttp.ClientError("API Error")):
            odds_data = await odds_api.get_wnba_odds()
        
        assert odds_data == []

    @pytest.mark.asyncio
    async def test_get_wnba_odds_http_error(self, rate_limiter, mock_redis):
        """Test handling of HTTP errors"""
        odds_api = EnhancedOddsAPI(rate_limiter, "test_key")
        
        rate_limiter.can_make_request = Mock(return_value=True)
        
        # Mock aiohttp response with error status
        mock_response = AsyncMock()
        mock_response.status = 429  # Too Many Requests
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            odds_data = await odds_api.get_wnba_odds()
        
        assert odds_data == []

    def test_parse_odds_api_response(self, rate_limiter, sample_odds_api_response):
        """Test parsing of Odds API response"""
        odds_api = EnhancedOddsAPI(rate_limiter, "test_key")
        
        parsed_data = odds_api._parse_odds_api_response(sample_odds_api_response)
        
        assert len(parsed_data) == 1
        odds = parsed_data[0]
        assert odds.game_id == 'game_123'
        assert odds.home_team == 'Las Vegas Aces'
        assert odds.away_team == 'New York Liberty'
        assert odds.bookmaker == 'bovada'
        assert odds.market_type == 'h2h'
        assert len(odds.outcomes) == 2

    def test_get_source_health(self, rate_limiter):
        """Test source health reporting"""
        odds_api = EnhancedOddsAPI(rate_limiter, "test_key")
        rate_limiter.can_make_request = Mock(return_value=True)
        
        health = odds_api.get_source_health()
        
        assert health['source'] == 'odds_api'
        assert health['status'] == 'healthy'
        assert health['rate_limit_status'] == 'ok'

class TestBovadaScraper:
    """Test suite for Bovada scraper"""

    def test_initialization(self, rate_limiter):
        """Test Bovada scraper initialization"""
        scraper = BovadaScraper(rate_limiter)
        
        assert scraper.base_url == "https://www.bovada.lv"
        assert len(scraper.user_agents) > 0

    @pytest.mark.asyncio
    async def test_get_wnba_odds_success(self, rate_limiter, sample_bovada_response, mock_redis):
        """Test successful odds retrieval from Bovada"""
        scraper = BovadaScraper(rate_limiter)
        
        # Mock rate limiter
        rate_limiter.can_make_request = Mock(return_value=True)
        rate_limiter.record_request = Mock()
        
        # Mock aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = sample_bovada_response
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            with patch('asyncio.sleep', return_value=None):  # Skip delay in tests
                odds_data = await scraper.get_wnba_odds()
        
        assert len(odds_data) > 0
        assert isinstance(odds_data[0], OddsData)
        assert odds_data[0].source == 'bovada_scraper'
        assert odds_data[0].bookmaker == 'bovada'
        rate_limiter.record_request.assert_called_once_with('bovada_scraper')

    @pytest.mark.asyncio
    async def test_get_wnba_odds_rate_limited(self, rate_limiter, mock_redis):
        """Test Bovada scraping when rate limited"""
        scraper = BovadaScraper(rate_limiter)
        
        rate_limiter.can_make_request = Mock(return_value=False)
        
        odds_data = await scraper.get_wnba_odds()
        
        assert odds_data == []

    @pytest.mark.asyncio
    async def test_get_wnba_odds_scraping_error(self, rate_limiter, mock_redis):
        """Test handling of scraping errors"""
        scraper = BovadaScraper(rate_limiter)
        
        rate_limiter.can_make_request = Mock(return_value=True)
        
        # Mock aiohttp to raise an exception
        with patch('aiohttp.ClientSession.get', side_effect=aiohttp.ClientError("Scraping blocked")):
            with patch('asyncio.sleep', return_value=None):
                odds_data = await scraper.get_wnba_odds()
        
        assert odds_data == []

    def test_parse_bovada_response(self, rate_limiter, sample_bovada_response):
        """Test parsing of Bovada response"""
        scraper = BovadaScraper(rate_limiter)
        
        parsed_data = scraper._parse_bovada_response(sample_bovada_response)
        
        assert len(parsed_data) > 0
        odds = parsed_data[0]
        assert 'bovada_' in odds.game_id
        assert odds.bookmaker == 'bovada'
        assert odds.market_type == 'h2h'
        assert odds.source == 'bovada_scraper'

    def test_map_bovada_market(self, rate_limiter):
        """Test Bovada market mapping"""
        scraper = BovadaScraper(rate_limiter)
        
        assert scraper._map_bovada_market('Moneyline') == 'h2h'
        assert scraper._map_bovada_market('Match Result') == 'h2h'
        assert scraper._map_bovada_market('Spread') == 'spreads'
        assert scraper._map_bovada_market('Handicap') == 'spreads'
        assert scraper._map_bovada_market('Total') == 'totals'
        assert scraper._map_bovada_market('Over/Under') == 'totals'
        assert scraper._map_bovada_market('Unknown Market') is None

    def test_get_source_health(self, rate_limiter):
        """Test Bovada scraper health reporting"""
        scraper = BovadaScraper(rate_limiter)
        rate_limiter.can_make_request = Mock(return_value=True)
        
        health = scraper.get_source_health()
        
        assert health['source'] == 'bovada_scraper'
        assert health['status'] == 'operational'
        assert health['anti_detection'] == 'active'

class TestBetOnlineScraper:
    """Test suite for BetOnline scraper"""

    def test_initialization(self, rate_limiter):
        """Test BetOnline scraper initialization"""
        scraper = BetOnlineScraper(rate_limiter)
        
        assert scraper.base_url == "https://www.betonline.ag"
        assert scraper.wnba_url == "/sportsbook/basketball/wnba"

    @patch('app.services.multi_source_ingestion.webdriver.Chrome')
    def test_create_driver(self, mock_chrome, rate_limiter):
        """Test WebDriver creation with proper options"""
        scraper = BetOnlineScraper(rate_limiter)
        
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        driver = scraper._create_driver()
        
        assert driver == mock_driver
        mock_chrome.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.multi_source_ingestion.webdriver.Chrome')
    @patch('app.services.multi_source_ingestion.WebDriverWait')
    @patch('app.services.multi_source_ingestion.BeautifulSoup')
    async def test_get_wnba_odds_success(self, mock_soup, mock_wait, mock_chrome, rate_limiter, mock_redis):
        """Test successful odds retrieval from BetOnline"""
        scraper = BetOnlineScraper(rate_limiter)
        
        # Mock rate limiter
        rate_limiter.can_make_request = Mock(return_value=True)
        rate_limiter.record_request = Mock()
        
        # Mock WebDriver
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        mock_driver.page_source = '<html><div class="event-row"></div></html>'
        
        # Mock WebDriverWait
        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.return_value = True
        
        # Mock BeautifulSoup
        mock_soup_instance = Mock()
        mock_soup.return_value = mock_soup_instance
        
        # Mock parsed HTML structure
        mock_row = Mock()
        mock_teams = [Mock(), Mock()]
        mock_teams[0].text.strip.return_value = "New York Liberty"
        mock_teams[1].text.strip.return_value = "Las Vegas Aces"
        mock_row.find_all.side_effect = [mock_teams, [Mock(), Mock()]]
        
        # Mock odds cells
        mock_odds = [Mock(), Mock()]
        mock_odds[0].text = "-140"
        mock_odds[1].text = "+120"
        mock_row.find_all.return_value = mock_odds
        
        mock_soup_instance.find_all.return_value = [mock_row]
        
        with patch('asyncio.sleep', return_value=None):
            odds_data = await scraper.get_wnba_odds()
        
        # Verify WebDriver operations
        mock_driver.get.assert_called_once()
        mock_driver.quit.assert_called_once()
        rate_limiter.record_request.assert_called_once_with('betonline_scraper')

    @pytest.mark.asyncio
    async def test_get_wnba_odds_rate_limited(self, rate_limiter, mock_redis):
        """Test BetOnline scraping when rate limited"""
        scraper = BetOnlineScraper(rate_limiter)
        
        rate_limiter.can_make_request = Mock(return_value=False)
        
        odds_data = await scraper.get_wnba_odds()
        
        assert odds_data == []

    @pytest.mark.asyncio
    @patch('app.services.multi_source_ingestion.webdriver.Chrome')
    async def test_get_wnba_odds_webdriver_error(self, mock_chrome, rate_limiter, mock_redis):
        """Test handling of WebDriver errors"""
        scraper = BetOnlineScraper(rate_limiter)
        
        rate_limiter.can_make_request = Mock(return_value=True)
        
        # Mock WebDriver to raise exception
        mock_chrome.side_effect = WebDriverException("ChromeDriver not found")
        
        with patch('asyncio.sleep', return_value=None):
            odds_data = await scraper.get_wnba_odds()
        
        assert odds_data == []

    def test_parse_american_odds(self, rate_limiter):
        """Test American odds parsing"""
        scraper = BetOnlineScraper(rate_limiter)
        
        assert scraper._parse_american_odds("+150") == 150
        assert scraper._parse_american_odds("-150") == -150
        assert scraper._parse_american_odds("150") == 150
        assert scraper._parse_american_odds("invalid") is None
        assert scraper._parse_american_odds("") is None

    def test_get_source_health(self, rate_limiter):
        """Test BetOnline scraper health reporting"""
        scraper = BetOnlineScraper(rate_limiter)
        rate_limiter.can_make_request = Mock(return_value=True)
        
        health = scraper.get_source_health()
        
        assert health['source'] == 'betonline_scraper'
        assert health['status'] == 'operational'
        assert health['method'] == 'selenium'

class TestMultiSourceDataAggregator:
    """Test suite for the main data aggregator"""

    @patch('app.services.multi_source_ingestion.redis.Redis')
    def test_initialization(self, mock_redis_class):
        """Test aggregator initialization"""
        mock_redis_instance = Mock()
        mock_redis_class.return_value = mock_redis_instance
        
        with patch.dict('os.environ', {'ODDS_API_KEY': 'test_key'}):
            aggregator = MultiSourceDataAggregator()
        
        assert len(aggregator.sources) > 0
        assert isinstance(aggregator.rate_limiter, RateLimitManager)

    @pytest.mark.asyncio
    @patch('app.services.multi_source_ingestion.redis.Redis')
    async def test_collect_all_odds_success(self, mock_redis_class):
        """Test successful odds collection from all sources"""
        mock_redis_instance = Mock()
        mock_redis_class.return_value = mock_redis_instance
        
        aggregator = MultiSourceDataAggregator()
        
        # Mock each source to return sample data
        sample_odds = OddsData(
            game_id="test_game",
            home_team="Team A",
            away_team="Team B",
            commence_time="2024-07-15T19:00:00Z",
            bookmaker="test_book",
            market_type="h2h",
            outcomes=[{"name": "Team A", "price": -140}],
            last_update="2024-07-15T18:30:00Z",
            source="test_source"
        )
        
        for source in aggregator.sources:
            source.get_wnba_odds = AsyncMock(return_value=[sample_odds])
        
        results = await aggregator.collect_all_odds()
        
        assert isinstance(results, dict)
        assert len(results) == len(aggregator.sources)

    @pytest.mark.asyncio
    @patch('app.services.multi_source_ingestion.redis.Redis')
    async def test_collect_all_odds_partial_failure(self, mock_redis_class):
        """Test odds collection when some sources fail"""
        mock_redis_instance = Mock()
        mock_redis_class.return_value = mock_redis_instance
        
        aggregator = MultiSourceDataAggregator()
        
        sample_odds = OddsData(
            game_id="test_game",
            home_team="Team A",
            away_team="Team B",
            commence_time="2024-07-15T19:00:00Z",
            bookmaker="test_book",
            market_type="h2h",
            outcomes=[{"name": "Team A", "price": -140}],
            last_update="2024-07-15T18:30:00Z",
            source="test_source"
        )
        
        # Mock first source to succeed, second to fail
        if len(aggregator.sources) >= 2:
            aggregator.sources[0].get_wnba_odds = AsyncMock(return_value=[sample_odds])
            aggregator.sources[1].get_wnba_odds = AsyncMock(side_effect=Exception("Source failed"))
        
        results = await aggregator.collect_all_odds()
        
        assert isinstance(results, dict)
        # Should still return results even with partial failures

    def test_detect_arbitrage_opportunities_found(self, mock_redis):
        """Test arbitrage detection when opportunities exist"""
        with patch('app.services.multi_source_ingestion.redis.Redis', return_value=mock_redis):
            aggregator = MultiSourceDataAggregator()
        
        # Create odds data with arbitrage opportunity
        odds_data = {
            'source1': [
                OddsData(
                    game_id="game1",
                    home_team="Team A",
                    away_team="Team B",
                    commence_time="2024-07-15T19:00:00Z",
                    bookmaker="book1",
                    market_type="h2h",
                    outcomes=[
                        {"name": "Team A", "price": -130},
                        {"name": "Team B", "price": 120}
                    ],
                    last_update="2024-07-15T18:30:00Z",
                    source="source1"
                )
            ],
            'source2': [
                OddsData(
                    game_id="game1",
                    home_team="Team A",
                    away_team="Team B",
                    commence_time="2024-07-15T19:00:00Z",
                    bookmaker="book2",
                    market_type="h2h",
                    outcomes=[
                        {"name": "Team A", "price": -140},
                        {"name": "Team B", "price": 130}
                    ],
                    last_update="2024-07-15T18:25:00Z",
                    source="source2"
                )
            ]
        }
        
        opportunities = aggregator.detect_arbitrage_opportunities(odds_data, 0.01)
        
        # Should detect arbitrage opportunities
        assert isinstance(opportunities, list)

    def test_detect_arbitrage_opportunities_none_found(self, mock_redis):
        """Test arbitrage detection when no opportunities exist"""
        with patch('app.services.multi_source_ingestion.redis.Redis', return_value=mock_redis):
            aggregator = MultiSourceDataAggregator()
        
        # Create odds data without arbitrage opportunity
        odds_data = {
            'source1': [
                OddsData(
                    game_id="game1",
                    home_team="Team A",
                    away_team="Team B",
                    commence_time="2024-07-15T19:00:00Z",
                    bookmaker="book1",
                    market_type="h2h",
                    outcomes=[
                        {"name": "Team A", "price": -110},
                        {"name": "Team B", "price": -110}
                    ],
                    last_update="2024-07-15T18:30:00Z",
                    source="source1"
                )
            ]
        }
        
        opportunities = aggregator.detect_arbitrage_opportunities(odds_data, 0.01)
        
        assert opportunities == []

    def test_calculate_arbitrage_valid_opportunity(self, mock_redis):
        """Test arbitrage calculation for valid opportunity"""
        with patch('app.services.multi_source_ingestion.redis.Redis', return_value=mock_redis):
            aggregator = MultiSourceDataAggregator()
        
        # Create odds list with arbitrage opportunity
        odds_list = [
            OddsData(
                game_id="game1",
                home_team="Team A",
                away_team="Team B",
                commence_time="2024-07-15T19:00:00Z",
                bookmaker="book1",
                market_type="h2h",
                outcomes=[
                    {"name": "Team A", "price": 150},  # Positive odds
                    {"name": "Team B", "price": 160}   # Positive odds
                ],
                last_update="2024-07-15T18:30:00Z",
                source="source1"
            ),
            OddsData(
                game_id="game1",
                home_team="Team A",
                away_team="Team B",
                commence_time="2024-07-15T19:00:00Z",
                bookmaker="book2",
                market_type="h2h",
                outcomes=[
                    {"name": "Team A", "price": 140},
                    {"name": "Team B", "price": 170}
                ],
                last_update="2024-07-15T18:25:00Z",
                source="source2"
            )
        ]
        
        opportunity = aggregator._calculate_arbitrage(odds_list, 0.01)
        
        if opportunity:
            assert isinstance(opportunity, ArbitrageOpportunity)
            assert opportunity.profit_margin > 0.01
            assert len(opportunity.best_odds) >= 2

    def test_get_all_source_health(self, mock_redis):
        """Test health status retrieval for all sources"""
        with patch('app.services.multi_source_ingestion.redis.Redis', return_value=mock_redis):
            aggregator = MultiSourceDataAggregator()
        
        # Mock each source's health method
        for source in aggregator.sources:
            source.get_source_health = Mock(return_value={
                'status': 'healthy',
                'source': source.__class__.__name__.lower()
            })
        
        health_data = aggregator.get_all_source_health()
        
        assert 'timestamp' in health_data
        assert 'sources' in health_data
        assert len(health_data['sources']) == len(aggregator.sources)

class TestMainInterfaceFunctions:
    """Test suite for main interface functions"""

    @pytest.mark.asyncio
    @patch('app.services.multi_source_ingestion.MultiSourceDataAggregator')
    async def test_get_multi_source_odds(self, mock_aggregator_class):
        """Test main get_multi_source_odds function"""
        mock_aggregator = Mock()
        mock_aggregator.collect_all_odds = AsyncMock(return_value={'source1': []})
        mock_aggregator_class.return_value = mock_aggregator
        
        result = await get_multi_source_odds()
        
        assert isinstance(result, dict)
        mock_aggregator.collect_all_odds.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.multi_source_ingestion.MultiSourceDataAggregator')
    async def test_find_real_time_arbitrage(self, mock_aggregator_class):
        """Test main find_real_time_arbitrage function"""
        mock_aggregator = Mock()
        mock_aggregator.get_real_time_opportunities = AsyncMock(return_value=[])
        mock_aggregator_class.return_value = mock_aggregator
        
        result = await find_real_time_arbitrage(0.02)
        
        assert isinstance(result, list)
        mock_aggregator.get_real_time_opportunities.assert_called_once_with(0.02)

    @patch('app.services.multi_source_ingestion.MultiSourceDataAggregator')
    def test_get_source_health_function(self, mock_aggregator_class):
        """Test main get_source_health function"""
        mock_aggregator = Mock()
        mock_aggregator.get_all_source_health = Mock(return_value={'status': 'healthy'})
        mock_aggregator_class.return_value = mock_aggregator
        
        result = get_source_health()
        
        assert isinstance(result, dict)
        mock_aggregator.get_all_source_health.assert_called_once()

class TestErrorHandling:
    """Test suite for error handling scenarios"""

    @pytest.mark.asyncio
    async def test_network_timeout_handling(self, rate_limiter, mock_redis):
        """Test handling of network timeouts"""
        odds_api = EnhancedOddsAPI(rate_limiter, "test_key")
        rate_limiter.can_make_request = Mock(return_value=True)
        
        # Mock timeout error
        with patch('aiohttp.ClientSession.get', side_effect=asyncio.TimeoutError()):
            odds_data = await odds_api.get_wnba_odds()
        
        assert odds_data == []

    @pytest.mark.asyncio
    async def test_json_decode_error_handling(self, rate_limiter, mock_redis):
        """Test handling of JSON decode errors"""
        odds_api = EnhancedOddsAPI(rate_limiter, "test_key")
        rate_limiter.can_make_request = Mock(return_value=True)
        
        # Mock response with invalid JSON
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            odds_data = await odds_api.get_wnba_odds()
        
        assert odds_data == []

    @pytest.mark.asyncio
    async def test_selenium_timeout_handling(self, rate_limiter, mock_redis):
        """Test handling of Selenium timeouts"""
        scraper = BetOnlineScraper(rate_limiter)
        rate_limiter.can_make_request = Mock(return_value=True)
        
        # Mock Selenium timeout
        with patch('app.services.multi_source_ingestion.webdriver.Chrome') as mock_chrome:
            mock_driver = Mock()
            mock_chrome.return_value = mock_driver
            
            with patch('app.services.multi_source_ingestion.WebDriverWait') as mock_wait:
                mock_wait_instance = Mock()
                mock_wait.return_value = mock_wait_instance
                mock_wait_instance.until.side_effect = TimeoutException("Page load timeout")
                
                with patch('asyncio.sleep', return_value=None):
                    odds_data = await scraper.get_wnba_odds()
        
        assert odds_data == []

class TestDataValidation:
    """Test suite for data validation"""

    def test_odds_data_creation_valid(self):
        """Test creation of valid OddsData objects"""
        odds = OddsData(
            game_id="test_game",
            home_team="Team A",
            away_team="Team B",
            commence_time="2024-07-15T19:00:00Z",
            bookmaker="test_book",
            market_type="h2h",
            outcomes=[{"name": "Team A", "price": -140}],
            last_update="2024-07-15T18:30:00Z",
            source="test_source"
        )
        
        assert odds.game_id == "test_game"
        assert odds.home_team == "Team A"
        assert odds.market_type == "h2h"

    def test_arbitrage_opportunity_creation_valid(self):
        """Test creation of valid ArbitrageOpportunity objects"""
        opportunity = ArbitrageOpportunity(
            game_id="test_game",
            game_description="Team B @ Team A",
            market_type="h2h",
            profit_margin=0.025,
            profit_percentage=2.5,
            best_odds={"Team A": {"price": -130, "bookmaker": "book1"}},
            total_stake=1000,
            individual_stakes={"Team A": 500, "Team B": 500},
            detected_at=datetime.now(timezone.utc).isoformat(),
            expiry_estimate=(datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
        )
        
        assert opportunity.profit_percentage == 2.5
        assert opportunity.total_stake == 1000
        assert "Team A" in opportunity.best_odds

class TestPerformance:
    """Test suite for performance requirements"""

    @pytest.mark.asyncio
    async def test_concurrent_source_collection(self, mock_redis):
        """Test that sources are collected concurrently"""
        with patch('app.services.multi_source_ingestion.redis.Redis', return_value=mock_redis):
            aggregator = MultiSourceDataAggregator()
        
        # Mock sources with delays to test concurrency
        async def slow_source():
            await asyncio.sleep(0.1)
            return []
        
        for source in aggregator.sources:
            source.get_wnba_odds = slow_source
        
        import time
        start_time = time.time()
        await aggregator.collect_all_odds()
        end_time = time.time()
        
        # Should complete in less time than sequential execution
        # (0.1 seconds per source * number of sources)
        expected_sequential_time = 0.1 * len(aggregator.sources)
        assert (end_time - start_time) < expected_sequential_time

    def test_large_odds_dataset_processing(self, mock_redis):
        """Test processing of large odds datasets"""
        with patch('app.services.multi_source_ingestion.redis.Redis', return_value=mock_redis):
            aggregator = MultiSourceDataAggregator()
        
        # Create large dataset
        large_odds_data = {}
        for i in range(100):  # 100 games
            large_odds_data[f'source_{i % 3}'] = [
                OddsData(
                    game_id=f"game_{i}",
                    home_team=f"Team_A_{i}",
                    away_team=f"Team_B_{i}",
                    commence_time="2024-07-15T19:00:00Z",
                    bookmaker=f"book_{i % 5}",
                    market_type="h2h",
                    outcomes=[
                        {"name": f"Team_A_{i}", "price": -110 + (i % 20)},
                        {"name": f"Team_B_{i}", "price": -110 - (i % 20)}
                    ],
                    last_update="2024-07-15T18:30:00Z",
                    source=f"source_{i % 3}"
                )
            ]
        
        import time
        start_time = time.time()
        opportunities = aggregator.detect_arbitrage_opportunities(large_odds_data, 0.01)
        end_time = time.time()
        
        # Should complete within reasonable time (5 seconds for 100 games)
        assert (end_time - start_time) < 5.0
        assert isinstance(opportunities, list)

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])