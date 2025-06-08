# WNBA Arbitrage AI Tool - API Research Documentation

## Day 2: Sportsbook API Research & Setup

### 📊 Primary Data Sources Analyzed

## 1. The Odds API (Primary Recommendation)

**Website**: https://the-odds-api.com/  
**Status**: ✅ **RECOMMENDED** - Best option for WNBA odds  
**Cost**: Free tier available (500 requests/month)

### Key Features:
- **WNBA Coverage**: Full WNBA season coverage with real-time odds
- **Bookmaker Coverage**: 40+ offshore and US sportsbooks including:
  - **Offshore Books**: Bovada, MyBookie, BetOnline, Heritage Sports, GTBets
  - **US Books**: FanDuel, DraftKings, Caesars, BetMGM
- **Markets**: Moneyline (H2H), Point Spreads, Totals (Over/Under)
- **Data Format**: Clean JSON with consistent structure
- **Rate Limits**: 500 requests/month (free), paid plans up to 10,000/month
- **Regions**: US, US2 (covers offshore books)

### API Details:
```
Endpoint: https://api.the-odds-api.com/v4/sports/basketball_wnba/odds
Authentication: API Key (query parameter)
Response Format: JSON
Rate Limiting: Monthly quota system
```

### Pros:
- ✅ Excellent WNBA coverage during season
- ✅ Includes major offshore sportsbooks
- ✅ Clean, well-documented API
- ✅ Reliable uptime and data quality
- ✅ Free tier sufficient for development/testing

### Cons:
- ❌ Limited free tier (500 requests/month)
- ❌ Paid plans can be expensive for high-volume usage
- ❌ No historical odds data in free tier

---

## 2. Offshore Sportsbook APIs/Scraping

### 2.1 Bovada
**Status**: ⚠️ **COMPLEX** - No public API, requires scraping  
**Popularity**: Very high among California bettors

**Technical Approach**:
- Web scraping required (dynamic content)
- Uses React/JavaScript rendering
- Requires sophisticated scraping tools (Selenium/Playwright)
- Anti-bot measures in place

### 2.2 MyBookie
**Status**: ⚠️ **COMPLEX** - No public API  
**Technical Notes**: Similar to Bovada, requires custom scraping solution

### 2.3 BetOnline
**Status**: ⚠️ **MODERATE** - Some API endpoints discoverable  
**Technical Notes**: Easier to scrape than Bovada but still requires custom solution

### 2.4 Heritage Sports
**Status**: ⚠️ **MODERATE** - Traditional HTML structure  
**Technical Notes**: More straightforward scraping but still no official API

---

## 3. Alternative Data Sources (Evaluated but not prioritized)

### 3.1 Pinnacle API
- **Status**: Available but requires approval
- **Focus**: Sharp/professional betting odds
- **Issue**: Limited recreational bettor appeal

### 3.2 Betfair API
- **Status**: Available via Exchange API
- **Issue**: Different betting model (exchange vs. sportsbook)
- **Coverage**: Limited WNBA coverage

### 3.3 SportRadar
- **Status**: Enterprise-level, expensive
- **Coverage**: Excellent but cost-prohibitive for MVP

---

## 🚀 Implementation Strategy

### Phase 1: The Odds API Integration (Current)
1. **Free Tier Setup**: 500 requests/month for development
2. **WNBA Focus**: Target `basketball_wnba` sport key
3. **Key Markets**: Moneyline, spreads, totals
4. **Offshore Coverage**: Focus on US2 region for offshore books

### Phase 2: Scraping Enhancement (Future)
1. **Bovada Scraper**: Custom implementation for California's most popular offshore book
2. **Rate Limiting**: Respectful scraping with delays
3. **Data Normalization**: Convert scraped data to match The Odds API format

### Phase 3: Premium Sources (Scale)
1. **Paid Odds API**: Upgrade to higher tier for more requests
2. **Multiple Sources**: Add redundancy and coverage
3. **Real-time Updates**: WebSocket connections for live odds

---

## 🔑 Required API Keys

### Immediate Need (Day 2):
1. **The Odds API Key**
   - Sign up at: https://the-odds-api.com/
   - Free account provides 500 requests/month
   - Set environment variable: `ODDS_API_KEY=your_key_here`

### Optional/Future:
2. **Backup Services** (for redundancy)
   - RapidAPI Sports Odds
   - SportsDataIO

---

## 📊 Data Structure Analysis

### The Odds API Response Format:
```json
{
  "id": "game_unique_id",
  "sport_key": "basketball_wnba",
  "sport_title": "WNBA",
  "commence_time": "2024-07-15T19:00:00Z",
  "home_team": "Las Vegas Aces",
  "away_team": "New York Liberty",
  "bookmakers": [
    {
      "key": "bovada",
      "title": "Bovada",
      "last_update": "2024-07-15T18:30:00Z",
      "markets": [
        {
          "key": "h2h",
          "last_update": "2024-07-15T18:30:00Z",
          "outcomes": [
            {
              "name": "Las Vegas Aces",
              "price": -140
            },
            {
              "name": "New York Liberty",
              "price": +120
            }
          ]
        }
      ]
    }
  ]
}
```

### Key Bookmakers Available:
- `bovada` - Bovada (Offshore)
- `mybookie` - MyBookie (Offshore)
- `betonline` - BetOnline (Offshore)
- `heritage` - Heritage Sports (Offshore)
- `gtbets` - GTBets (Offshore)
- `fanduel` - FanDuel (US Legal)
- `draftkings` - DraftKings (US Legal)

---

## ⚡ Rate Limiting Strategy

### The Odds API Limits:
- **Free Tier**: 500 requests/month
- **Conservative Usage**: 1 request per minute during active periods
- **Smart Caching**: Cache results for 5-10 minutes
- **Game-Day Focus**: Increase frequency 2-3 hours before games

### Optimization Techniques:
1. **Bulk Requests**: Get all games in single API call
2. **Selective Updates**: Only fetch odds for games within 24 hours
3. **Diff Detection**: Only process changed odds
4. **Off-Season Handling**: Minimal requests when WNBA not active

---

## 🎯 Arbitrage Detection Logic

### Basic Arbitrage Formula:
```
Total Implied Probability = Sum(1/Decimal_Odds_per_Outcome)
Arbitrage Exists when: Total Implied Probability < 1.0
Profit Margin = 1 - Total Implied_Probability
```

### American Odds Conversion:
```python
# Positive odds (+150) to implied probability
implied_prob = 100 / (odds + 100)

# Negative odds (-150) to implied probability  
implied_prob = abs(odds) / (abs(odds) + 100)
```

### Minimum Viable Arbitrage:
- **Target**: 1-3% profit margin minimum
- **Sweet Spot**: 2-5% profit opportunities
- **Alert Threshold**: 3%+ for immediate notifications

---

## 🔧 Technical Implementation Status

### ✅ Completed:
- The Odds API service class
- Arbitrage detection algorithm
- FastAPI endpoints for odds and arbitrage
- Rate limiting and error handling
- Comprehensive test suite
- Provider status monitoring

### 🚧 In Development:
- Real-time odds monitoring
- Advanced caching strategy
- Webhook notifications

### 📋 Next Steps (Day 3):
- Database schema for odds storage
- Historical data tracking
- Alert system foundation

---

## 🎮 Testing Instructions

### Without API Key:
```bash
# Test service initialization (graceful failure)
python app/services/odds_api.py

# Run unit tests
pytest tests/test_odds_api.py -v
```

### With API Key:
```bash
# Set environment variable
export ODDS_API_KEY="your_actual_api_key_here"

# Test live data fetching
python app/services/odds_api.py

# Test API endpoints
curl http://localhost:8000/api/v1/odds/health
curl http://localhost:8000/api/v1/odds/providers/status
```

### Full Integration Test:
```bash
# Start the server
python app/main.py

# Test endpoints
curl "http://localhost:8000/api/v1/odds/"
curl "http://localhost:8000/api/v1/odds/arbitrage?min_profit=0.01"
curl "http://localhost:8000/api/v1/odds/arbitrage/summary"
```

---

## 💰 Cost Analysis

### Development Phase (MVP):
- **The Odds API Free**: $0/month (500 requests)
- **Total Monthly Cost**: $0

### Production Phase (Estimated):
- **The Odds API Standard**: $79/month (10,000 requests)
- **Server Hosting**: $20-50/month
- **Database**: $10-25/month
- **Total Monthly Cost**: ~$110-155/month

### Scale Phase:
- **The Odds API Premium**: $199/month (50,000 requests)
- **Additional scraping infrastructure**: $100-200/month
- **Enhanced hosting**: $100-200/month
- **Total Monthly Cost**: ~$400-600/month

---

## 🚨 Important Notes

1. **WNBA Season**: May - October (peak usage period)
2. **Off-Season Strategy**: Minimal API usage, focus on other sports data
3. **Legal Compliance**: Ensure all data usage complies with terms of service
4. **Scraping Ethics**: Respectful scraping with appropriate delays
5. **Data Freshness**: Odds change rapidly, especially close to game time

---

*This documentation will be updated as we implement and test the various data sources.* 