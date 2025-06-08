# Enhanced Data Ingestion Setup Guide

## 🚀 Quick Start

This guide will help you set up the enhanced multi-source data ingestion system for profitable WNBA arbitrage detection.

### Prerequisites

1. **Python 3.11+** with virtual environment
2. **Redis** for caching and rate limiting
3. **Chrome/Chromium** for web scraping
4. **API Keys** (see below)

---

## 📋 Step-by-Step Setup

### 1. Install Enhanced Dependencies

```bash
# Activate your virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install new dependencies
pip install -r requirements.txt

# Install Chrome WebDriver (for scraping)
# On macOS:
brew install chromedriver

# On Ubuntu:
sudo apt-get install chromium-chromedriver

# On Windows:
# Download from: https://chromedriver.chromium.org/
```

### 2. Set Up Redis (Required for Rate Limiting)

#### Option A: Local Redis Installation
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu
sudo apt-get install redis-server
sudo systemctl start redis

# Windows
# Download from: https://redis.io/download
```

#### Option B: Redis Cloud (Recommended for Production)
```bash
# Sign up at: https://cloud.redis.com/
# Get connection details and add to .env file
```

### 3. Configure Environment Variables

Create or update your `.env` file:

```bash
# Core API Keys
ODDS_API_KEY=your_odds_api_key_here

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
# For Redis Cloud: REDIS_URL=rediss://username:password@host:port

# Environment Setting
ENVIRONMENT=development  # or 'staging' or 'production'

# Scraping Configuration (Optional)
CAPTCHA_SERVICE_KEY=your_2captcha_key  # For Bovada if needed
PROXY_SERVICE_URL=http://your-proxy-service  # For production

# Rate Limiting (Optional - uses defaults if not set)
BOVADA_RATE_LIMIT_PER_MINUTE=0.5
BETONLINE_RATE_LIMIT_PER_MINUTE=1.0

# Monitoring (Optional)
SENTRY_DSN=your_sentry_dsn  # For error tracking
```

### 4. Test the Enhanced System

#### 4.1 Test Individual Components
```bash
# Test Redis connection
python -c "import redis; r = redis.Redis(); print('Redis:', r.ping())"

# Test basic multi-source ingestion
python app/services/multi_source_ingestion.py

# Test configuration
python app/config/data_sources.py
```

#### 4.2 Test API Endpoints
```bash
# Start the enhanced server
python app/main.py

# Test new multi-source endpoints
curl "http://localhost:8000/api/v2/odds/"
curl "http://localhost:8000/api/v2/odds/arbitrage/real-time"
curl "http://localhost:8000/api/v2/odds/sources/status"
```

---

## 🔧 Configuration Options

### Data Sources Priority

Edit `app/config/data_sources.py` to customize:

```python
DATA_SOURCES = {
    'odds_api': SourceConfig(
        enabled=True,           # Enable/disable source
        rate_limit_per_minute=60,  # Requests per minute
        priority=1,             # 1 = highest priority
        timeout=30,             # Request timeout
        retry_attempts=3        # Retry failed requests
    ),
    'bovada_scraper': SourceConfig(
        enabled=True,
        rate_limit_per_minute=0.5,  # Every 2 minutes
        priority=2,
        timeout=45,
        retry_attempts=2
    )
}
```

### Arbitrage Detection Settings

```python
ARBITRAGE_CONFIG = {
    'min_profit_margin': 0.015,      # 1.5% minimum profit
    'max_profit_margin': 0.20,       # 20% maximum (error detection)
    'min_bookmakers': 2,             # Minimum sources required
    'execution_window': 600,         # 10 minutes window
}
```

### Environment-Specific Settings

- **Development**: Conservative rate limits, extensive logging
- **Staging**: Moderate collection, reduced caching
- **Production**: Aggressive collection, optimized performance

---

## 📊 Available Data Sources

### Tier 1: API Sources (Most Reliable)
1. **The Odds API** ✅
   - Coverage: 40+ sportsbooks including offshore
   - Rate Limit: 500 requests/month (free), 10,000/month ($79)
   - Reliability: 99.9% uptime
   - Setup: Add `ODDS_API_KEY` to .env

### Tier 2: Scraping Sources (Higher Volume)
2. **Bovada Scraper** ✅
   - California's most popular offshore book
   - Rate Limit: Every 2 minutes (conservative)
   - Setup: Automatic (requires Chrome)

3. **BetOnline Scraper** ✅
   - Reliable offshore alternative
   - Rate Limit: Every minute
   - Setup: Automatic (requires Chrome)

### Tier 3: Future Sources (Planned)
4. **MyBookie Scraper** (Coming Soon)
5. **Betfair Exchange API** (Real-time data)
6. **News APIs** (Breaking updates)

---

## 🚀 New API Endpoints

### Enhanced Multi-Source Endpoints

#### Get Multi-Source Odds
```http
GET /api/v2/odds/
?sources=odds_api,bovada_scraper
&bookmakers=bovada,betonline
&markets=h2h,spreads
&fresh_only=true
```

#### Real-Time Arbitrage Detection
```http
GET /api/v2/odds/arbitrage/real-time
?min_profit=0.02
&max_opportunities=10
&include_execution_plan=true
```

#### Market Analysis Summary
```http
GET /api/v2/odds/arbitrage/summary
?min_profit=0.015
&lookback_hours=6
```

#### Source Health Monitoring
```http
GET /api/v2/odds/sources/status
```

#### Single Source Data
```http
GET /api/v2/odds/sources/bovada_scraper/odds
?markets=h2h,spreads
```

#### Execution Simulation
```http
POST /api/v2/odds/arbitrage/simulate
{
  "opportunity_data": {...},
  "total_stake": 1000,
  "include_fees": true,
  "risk_tolerance": "medium"
}
```

---

## 🔍 Monitoring and Debugging

### Health Checks
```bash
# Check overall system health
curl "http://localhost:8000/api/v2/odds/health"

# Check individual source status
curl "http://localhost:8000/api/v2/odds/sources/status"
```

### Redis Monitoring
```bash
# Connect to Redis CLI
redis-cli

# Check rate limiting data
KEYS rate_limit:*

# Check cached odds
KEYS odds_data:*

# Monitor Redis activity
MONITOR
```

### Log Analysis
```bash
# Check application logs
tail -f app.log

# Filter for specific sources
grep "bovada_scraper" app.log
grep "arbitrage" app.log
```

---

## ⚡ Performance Optimization

### Production Optimizations

1. **Upgrade The Odds API**
```bash
# Upgrade to paid tier for better rate limits
# $79/month = 10,000 requests vs 500 free
```

2. **Enable Proxy Rotation**
```python
# In production environment
SCRAPING_CONFIG.proxy_enabled = True
SCRAPING_CONFIG.proxy_rotation = True
```

3. **Optimize Redis**
```bash
# Use Redis persistence
redis-server --appendonly yes

# Configure memory limits
redis-cli config set maxmemory 256mb
redis-cli config set maxmemory-policy allkeys-lru
```

4. **Scale Horizontally**
```bash
# Run multiple scraper instances
# Use load balancer for API endpoints
# Implement database connection pooling
```

### Rate Limit Optimization

```python
# Adjust for peak times
if is_peak_season('basketball_wnba'):
    DATA_SOURCES['bovada_scraper'].rate_limit_per_minute = 1.0
    
# Game day optimization
if is_game_day():
    increase_collection_frequency()
```

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Chrome Driver Issues
```bash
# Error: chromedriver not found
# Solution: Install chromedriver and add to PATH
brew install chromedriver  # macOS
sudo apt-get install chromium-chromedriver  # Ubuntu
```

#### 2. Redis Connection Failed
```bash
# Error: ConnectionError
# Solution: Start Redis service
brew services start redis  # macOS
sudo systemctl start redis  # Ubuntu
```

#### 3. Rate Limit Exceeded
```python
# Error: Too many requests
# Solution: Check rate limiting in Redis
redis-cli KEYS "rate_limit:*"
redis-cli FLUSHDB  # Clear rate limits (development only)
```

#### 4. Scraping Blocked
```bash
# Error: 403 Forbidden or CAPTCHA
# Solution: Enable proxy rotation and reduce frequency
SCRAPING_CONFIG.proxy_enabled = True
DATA_SOURCES['bovada_scraper'].rate_limit_per_minute = 0.25
```

#### 5. Import Errors
```bash
# Error: Module not found
# Solution: Install missing dependencies
pip install -r requirements.txt
pip install webdriver-manager
```

### Performance Issues

#### Slow Response Times
1. Check Redis connection latency
2. Optimize database queries  
3. Enable response caching
4. Use async/await properly

#### Memory Usage
1. Implement data retention policies
2. Clear old cached data
3. Monitor Redis memory usage
4. Use pagination for large datasets

#### High Error Rates
1. Enable detailed logging
2. Implement exponential backoff
3. Add circuit breakers
4. Monitor source health continuously

---

## 💰 Cost Optimization

### Free Tier Limits
- **The Odds API**: 500 requests/month
- **Redis Cloud**: 30MB storage
- **Chrome**: Free browser automation

### Paid Tier Recommendations
- **The Odds API Standard**: $79/month (10,000 requests)
- **Redis Cloud**: $15/month (100MB)
- **VPS**: $25/month (dedicated scraping)

### Cost-Effective Scaling
1. Start with free tiers for development
2. Upgrade The Odds API first (highest ROI)
3. Add Redis Cloud for reliability
4. Scale scraping infrastructure last

---

## 🎯 Next Steps

After setting up the enhanced data ingestion:

1. **Monitor Performance** for 24-48 hours
2. **Optimize Rate Limits** based on success rates
3. **Add Real-Time Alerts** for high-profit opportunities
4. **Implement ML Models** for prediction enhancement
5. **Build Frontend Dashboard** for user interface

### Integration with ML Pipeline
```python
# Coming in Phase 2
from app.ml.arbitrage_predictor import predict_opportunity_success
from app.ml.line_movement_predictor import predict_line_changes
from app.llm.news_analyzer import analyze_market_impact
```

---

## 📞 Support

### Get Help
- 📖 **Documentation**: Check `data_ingestion_strategy.md`
- 🐛 **Issues**: Report bugs in GitHub issues
- 💬 **Questions**: Use project discussions
- 📧 **Contact**: For urgent production issues

### Contributing
- 🔧 **Improvements**: Submit pull requests
- 📝 **Documentation**: Help improve guides
- 🧪 **Testing**: Add test cases
- 💡 **Features**: Suggest enhancements

---

**Status**: Enhanced multi-source data ingestion ready for WNBA 2025 season! 🏀⚡