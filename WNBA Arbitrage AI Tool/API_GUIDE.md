# API Testing and Usage Guide

## Quick Start

### Prerequisites
- Python 3.11+
- The Odds API key (get free tier at [The Odds API](https://the-odds-api.com/))

### Installation & Setup
```bash
# 1. Clone and navigate
git clone https://github.com/AKarode/WNBA-Arbitrage-AI-Tool.git
cd WNBA-Arbitrage-AI-Tool

# 2. Set up environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure API key
echo "ODDS_API_KEY=your_api_key_here" > .env

# 4. Run the application
python app/main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Core Endpoints

#### Health Check
```bash
GET /health
curl http://localhost:8000/health
```

#### Supported Sports
```bash
GET /sports
curl http://localhost:8000/sports
```

### Enhanced Arbitrage API (Recommended)

#### Single Sport Arbitrage Detection
```bash
GET /api/enhanced/arbitrage/{sport_key}
curl "http://localhost:8000/api/enhanced/arbitrage/basketball_wnba?min_profit=1.0"
```

**Parameters:**
- `min_profit` (float): Minimum profit margin % (default: 1.0)
- `enable_cross_market` (bool): Enable cross-market detection (default: true)
- `include_spreads` (bool): Include spread arbitrage (default: true)
- `include_totals` (bool): Include totals arbitrage (default: true)
- `confidence_threshold` (float): Minimum confidence score (default: 0.7)

#### Multi-Sport Parallel Scanning
```bash
GET /api/enhanced/arbitrage/all
curl "http://localhost:8000/api/enhanced/arbitrage/all?min_profit=1.0&max_sports=5"
```

**Parameters:**
- `min_profit` (float): Minimum profit margin %
- `max_sports` (int): Maximum sports to analyze (default: 10)
- `enable_parallel` (bool): Use parallel processing (default: true)
- `category_filter` (string): Filter by category (us_major, basketball, etc.)

#### Enhanced Sports List
```bash
GET /api/enhanced/sports
curl "http://localhost:8000/api/enhanced/sports?category=us_major"
```

#### System Status
```bash
GET /api/enhanced/system/status
curl http://localhost:8000/api/enhanced/system/status
```

### Legacy API Endpoints

#### Basic Odds
```bash
GET /api/odds/{sport_key}
curl http://localhost:8000/api/odds/basketball_wnba
```

#### Basic Arbitrage Detection
```bash
GET /api/arbitrage/{sport_key}
curl "http://localhost:8000/api/arbitrage/basketball_wnba?min_profit=2.0"
```

## Testing

### Run All Tests
```bash
# Run complete test suite
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=app --cov-report=html
```

### Test Categories
```bash
# Unit tests only
pytest tests/ -m unit -v

# Integration tests
pytest tests/ -m integration -v

# Performance tests
pytest tests/ -m performance -v

# API endpoint tests
pytest tests/ -m api -v

# Arbitrage detection tests
pytest tests/ -m arbitrage -v

# Parallel processing tests
pytest tests/ -m parallel -v

# Cross-market arbitrage tests
pytest tests/ -m cross_market -v
```

### Individual Test Files
```bash
# Enhanced arbitrage detection
pytest tests/test_enhanced_arbitrage_detection.py -v

# Cross-market arbitrage
pytest tests/test_cross_market_arbitrage.py -v

# Parallel processing
pytest tests/test_parallel_processing.py -v

# Integration tests
pytest tests/test_integration_enhanced_system.py -v
```

## Interactive API Documentation

Access the auto-generated interactive documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Example API Responses

### Arbitrage Opportunity Response
```json
{
  "sport": {
    "key": "basketball_wnba",
    "title": "WNBA", 
    "category": "basketball",
    "scanning_mode": "enhanced"
  },
  "analysis": {
    "total_games_analyzed": 3,
    "opportunities_found": 1,
    "processing_time_ms": 125,
    "enhanced_opportunities": [
      {
        "game": {
          "home_team": "Los Angeles Sparks",
          "away_team": "Golden State Valkyries"
        },
        "arbitrage": {
          "profit_margin": 21.22,
          "market_type": "moneyline",
          "confidence_score": 0.95,
          "best_odds": {
            "Team A": {
              "price": 2.20,
              "bookmaker": "bookmaker1"
            },
            "Team B": {
              "price": 3.00,
              "bookmaker": "bookmaker2" 
            }
          }
        },
        "optimal_stakes": {
          "Team A": 4545.45,
          "Team B": 3333.33
        }
      }
    ]
  }
}
```

### Multi-Sport Scanning Response
```json
{
  "scan_summary": {
    "sports_analyzed": 3,
    "total_games": 8,
    "total_opportunities": 2,
    "processing_time_ms": 850,
    "parallel_processing": true
  },
  "sport_breakdown": {
    "basketball_wnba": {
      "games": 3,
      "opportunities": 1,
      "sport_title": "WNBA"
    },
    "basketball_nba": {
      "games": 5,
      "opportunities": 1,
      "sport_title": "NBA"
    }
  },
  "all_opportunities": [...]
}
```

## Supported Sports

The system supports 47+ sports including:

**US Major Sports:**
- NBA (`basketball_nba`)
- WNBA (`basketball_wnba`) 
- NFL (`americanfootball_nfl`)
- MLB (`baseball_mlb`)
- NHL (`icehockey_nhl`)
- MLS (`soccer_usa_mls`)

**International Sports:**
- English Premier League (`soccer_epl`)
- La Liga (`soccer_spain_la_liga`)
- Bundesliga (`soccer_germany_bundesliga`)
- Serie A (`soccer_italy_serie_a`)
- UFC (`mma_ufc`)
- And 40+ more...

## Performance

- **API Response Time**: <200ms for single sport
- **Multi-Sport Scanning**: <1000ms for 10 sports
- **Parallel Processing**: Up to 10 concurrent requests
- **Arbitrage Detection**: 95%+ accuracy with 21%+ profit detection in test scenarios

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Sport not found
- `500`: Internal server error

Error responses include descriptive messages:
```json
{
  "detail": "Sport 'invalid_sport' not supported. Use /api/enhanced/sports for available sports."
}
```

## Configuration

The system uses sport-specific configurations for optimal performance:
- **Update frequencies**: 30s (NBA/NFL) to 120s (MLB)
- **Profit thresholds**: 1.0% (NFL) to 2.5% (Golf)
- **Peak season awareness**: Automatic seasonal adjustments
- **Offshore bookmaker focus**: BetOnline, Bovada, BetUS priority