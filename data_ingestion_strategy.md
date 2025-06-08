# WNBA Arbitrage AI Tool - Data Ingestion Strategy

## 🎯 Multi-Source Data Architecture

### Primary Data Sources (Tier 1)
1. **The Odds API** - Legitimate, reliable baseline
2. **BetMGM API** - Official US sportsbook with API access
3. **Pinnacle API** - Sharp book for line validation

### Secondary Data Sources (Tier 2) 
4. **Bovada Scraping** - Highest volume offshore book
5. **BetOnline Scraping** - Reliable offshore alternative
6. **MyBookie Scraping** - Good arbitrage opportunities

### Tertiary Data Sources (Tier 3)
7. **Betfair Exchange** - Real-time market sentiment
8. **Twitter API** - Breaking news and line movement alerts
9. **ESPN/WNBA APIs** - Injury reports and game info

---

## 🏗️ Technical Implementation Plan

### Phase 1: Enhanced API Integration (Week 1-2)

#### 1.1 Upgrade The Odds API Usage
```python
# Current: 500 requests/month (free)
# Upgrade to: 10,000 requests/month ($79/month)
# Strategy: 1 request every 6 minutes during active periods

ODDS_API_CONFIG = {
    'base_requests_per_day': 300,  # Conservative daily limit
    'game_day_multiplier': 3,      # Increase frequency on game days
    'live_game_multiplier': 6,     # Every minute during live games
    'markets': ['h2h', 'spreads', 'totals', 'player_props'],
    'regions': ['us', 'us2', 'uk', 'au'],  # Include offshore coverage
}
```

#### 1.2 Add BetMGM Official API
```python
# BetMGM provides official API access for licensed operators
# Apply for developer access for sports data
BETMGM_CONFIG = {
    'endpoint': 'https://api.betmgm.com/v1/sports/basketball/wnba',
    'rate_limit': '100 requests/hour',
    'markets': ['moneyline', 'spread', 'total', 'player_props'],
    'update_frequency': '30 seconds'
}
```

### Phase 2: Strategic Scraping Implementation (Week 2-3)

#### 2.1 Bovada Scraper (Priority #1)
```python
# Bovada Technical Specs:
# - React-based SPA with dynamic content
# - CloudFlare protection + reCAPTCHA
# - JSON endpoints for odds data
# - 30-second odds updates

class BovadaScraper:
    def __init__(self):
        self.base_url = "https://www.bovada.lv"
        self.wnba_endpoint = "/services/sports/event/coupon/events/A/description/basketball/wnba"
        self.session = self._create_session()
        
    def _create_session(self):
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.bovada.lv/sports/basketball/wnba',
        })
        return session
        
    def get_wnba_odds(self):
        # Implementation with proxy rotation and rate limiting
        # Target: Every 2-3 minutes during active periods
        pass
```

#### 2.2 BetOnline Scraper (Priority #2)  
```python
# BetOnline Technical Specs:
# - Traditional HTML with some AJAX
# - Basic SSL protection
# - More scraping-friendly than Bovada
# - 1-minute odds updates

class BetOnlineScraper:
    def __init__(self):
        self.base_url = "https://www.betonline.ag"
        self.wnba_url = "/sportsbook/basketball/wnba"
        
    def get_live_odds(self):
        # Use Selenium for dynamic content
        # Target: Every 1-2 minutes
        pass
```

#### 2.3 Proxy and Anti-Detection Strategy
```python
SCRAPING_CONFIG = {
    'proxy_rotation': True,
    'proxy_pool_size': 10,
    'request_delay': (120, 180),  # 2-3 minutes between requests
    'user_agent_rotation': True,
    'captcha_service': '2captcha',  # For Bovada reCAPTCHA
    'max_retries': 3,
    'timeout': 30,
}
```

### Phase 3: Real-Time Data Pipeline (Week 3-4)

#### 3.1 Event-Driven Architecture
```python
# Use Redis Pub/Sub for real-time updates
import redis
import asyncio

class RealTimeOddsProcessor:
    def __init__(self):
        self.redis_client = redis.Redis()
        self.subscribers = []
        
    async def process_odds_update(self, source, odds_data):
        # 1. Validate and normalize data
        # 2. Detect arbitrage opportunities  
        # 3. Publish to subscribers
        # 4. Store in time-series database
        
        arbitrage_opps = self.detect_arbitrage(odds_data)
        if arbitrage_opps:
            await self.publish_arbitrage_alert(arbitrage_opps)
```

#### 3.2 WebSocket Streams for Live Data
```python
# Connect to Betfair Exchange for real-time market data
import websockets

async def betfair_stream_handler():
    uri = "wss://stream-api.betfair.com/api/betting/exchange/stream"
    async with websockets.connect(uri) as websocket:
        # Subscribe to WNBA markets
        # Process real-time price movements
        # Trigger arbitrage detection on significant moves
        pass
```

---

## 📊 Data Storage and Processing

### Time-Series Database for Odds History
```python
# Use InfluxDB for time-series odds data
from influxdb_client import InfluxDBClient

INFLUXDB_CONFIG = {
    'org': 'wnba_arbitrage',
    'bucket': 'odds_history',
    'retention_policy': '90d',  # Keep 90 days of historical data
    'measurement_frequency': '30s'  # Store odds every 30 seconds
}

# Schema:
# measurement: odds_update
# tags: bookmaker, team, market_type
# fields: price, implied_probability, timestamp
# time: auto-generated timestamp
```

### Redis Caching Strategy  
```python
REDIS_CONFIG = {
    'odds_cache_ttl': 60,      # Cache odds for 1 minute
    'arbitrage_cache_ttl': 30,  # Cache arbitrage calcs for 30 seconds
    'news_cache_ttl': 300,     # Cache news for 5 minutes
    'rate_limit_ttl': 3600,    # Track rate limits per hour
}
```

---

## 🚨 Rate Limiting and Reliability

### Smart Request Scheduling
```python
class RateLimitManager:
    def __init__(self):
        self.source_limits = {
            'odds_api': {'rpm': 60, 'daily': 300},
            'bovada_scraper': {'rpm': 0.5, 'daily': 720},  # Every 2 minutes
            'betonline_scraper': {'rpm': 1, 'daily': 1440}, # Every minute
        }
        
    def can_make_request(self, source):
        # Check against rate limits
        # Implement exponential backoff
        # Handle temporary failures gracefully
        pass
        
    def schedule_next_request(self, source, priority='normal'):
        # Priority queue for urgent arbitrage checks
        # Reduce frequency during off-peak hours
        # Increase frequency 2 hours before games
        pass
```

### Error Handling and Fallbacks
```python
class DataSourceManager:
    def __init__(self):
        self.primary_sources = ['odds_api', 'betmgm_api']
        self.fallback_sources = ['bovada_scraper', 'betonline_scraper']
        
    async def get_odds_with_fallback(self, game_id):
        for source in self.primary_sources:
            try:
                return await self.fetch_odds(source, game_id)
            except Exception as e:
                logging.warning(f"Primary source {source} failed: {e}")
                
        # Try fallback sources
        for source in self.fallback_sources:
            try:
                return await self.fetch_odds(source, game_id)
            except Exception as e:
                logging.error(f"Fallback source {source} failed: {e}")
                
        raise Exception("All data sources failed")
```

---

## 🔐 Legal and Compliance

### Terms of Service Compliance
```python
TOS_COMPLIANCE = {
    'request_delays': {
        'bovada': 120,     # 2 minutes minimum between requests
        'betonline': 60,   # 1 minute minimum  
        'mybookie': 90,    # 1.5 minutes minimum
    },
    'user_agent_disclosure': True,
    'respect_robots_txt': True,
    'no_login_required': True,  # Only scrape public odds
}
```

### Data Usage Rights
- **Public Odds Data**: Generally considered public information
- **Attribution**: Include source attribution in all displays
- **Commercial Use**: Ensure compliance with each site's terms
- **Rate Limiting**: Never overwhelm servers with requests

---

## 💰 Cost Analysis

### Monthly Data Costs
```
Primary Sources:
- The Odds API (Standard): $79/month
- BetMGM API: Free (requires approval)
- Pinnacle API: $50/month

Secondary Sources:
- Proxy service: $30/month
- CAPTCHA solving: $20/month
- VPS for scraping: $25/month

Infrastructure:
- InfluxDB Cloud: $25/month
- Redis Cloud: $15/month
- AWS hosting: $40/month

Total Monthly Cost: ~$284/month
```

### ROI Justification
- Target: Find 2-3 arbitrage opportunities per day
- Average opportunity: 2-4% profit margin  
- User base: 100 active bettors
- Average bet: $100
- Platform fee: 5% of profits

**Estimated monthly revenue**: $600-1200
**Monthly costs**: $284
**Net profit**: $316-916/month

---

## 🚀 Implementation Timeline

### Week 1: Foundation
- [x] Upgrade The Odds API to paid tier
- [ ] Implement basic Bovada scraper
- [ ] Set up Redis caching
- [ ] Add InfluxDB for time-series storage

### Week 2: Multi-Source Integration  
- [ ] Add BetOnline scraper
- [ ] Implement rate limiting manager
- [ ] Add proxy rotation system
- [ ] Create data normalization pipeline

### Week 3: Real-Time Pipeline
- [ ] Add WebSocket streams
- [ ] Implement event-driven architecture
- [ ] Create arbitrage detection engine
- [ ] Add real-time alerts

### Week 4: Optimization
- [ ] Performance tuning
- [ ] Error handling and fallbacks  
- [ ] Monitoring and alerting
- [ ] Load testing

---

## 📈 Success Metrics

### Data Quality Metrics
- **Uptime**: 99.5% data availability
- **Latency**: <30 seconds from odds change to detection
- **Accuracy**: 99%+ odds data accuracy vs manual verification
- **Coverage**: 90%+ of available WNBA games

### Arbitrage Detection Metrics  
- **Opportunities Found**: 5-10 per day during WNBA season
- **False Positives**: <5%
- **Execution Window**: Alert users within 60 seconds
- **Profit Margin**: 2-5% average opportunity size

This comprehensive data ingestion strategy provides multiple redundant sources, real-time processing, and scalable architecture for detecting profitable arbitrage opportunities in WNBA betting markets.