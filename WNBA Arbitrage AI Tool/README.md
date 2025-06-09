# Sports Arbitrage Detection System

<div align="center">

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Coverage](https://img.shields.io/badge/coverage-90%2B-brightgreen.svg)](https://github.com/AKarode/WNBA-Arbitrage-AI-Tool)

**AI-powered arbitrage detection platform for sports betting markets**

*47+ sports • Real-time analysis • California offshore-friendly*

</div>

## 🎯 Overview

AI-powered arbitrage detection system that identifies profitable betting opportunities across 47+ sports in real-time. Designed for California-based users accessing offshore sportsbooks (BetOnline, Bovada, BetUS).

**Key Features:**
- Multi-sport arbitrage detection with 95%+ accuracy
- Parallel processing for real-time analysis
- California offshore sportsbook focus
- Comprehensive test coverage and TDD methodology

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- The Odds API key ([free tier available](https://the-odds-api.com/))

### Installation
```bash
# Clone and setup
git clone https://github.com/AKarode/WNBA-Arbitrage-AI-Tool.git
cd WNBA-Arbitrage-AI-Tool

# Environment setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure API key
echo "ODDS_API_KEY=your_api_key_here" > .env

# Run application
python app/main.py
```

**API Available at:** `http://localhost:8000`  
**Interactive Docs:** `http://localhost:8000/docs`

## 📡 API Usage

### Key Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Enhanced arbitrage detection
curl "http://localhost:8000/api/enhanced/arbitrage/basketball_wnba?min_profit=1.0"

# Multi-sport parallel scanning
curl "http://localhost:8000/api/enhanced/arbitrage/all?max_sports=5"

# Supported sports list
curl http://localhost:8000/api/enhanced/sports

# System status
curl http://localhost:8000/api/enhanced/system/status
```

### Example Response
```json
{
  "sport": {"key": "basketball_wnba", "title": "WNBA"},
  "analysis": {
    "opportunities_found": 1,
    "enhanced_opportunities": [{
      "game": {"home_team": "Team A", "away_team": "Team B"},
      "arbitrage": {
        "profit_margin": 21.22,
        "confidence_score": 0.95,
        "best_odds": {
          "Team A": {"price": 2.20, "bookmaker": "bookmaker1"},
          "Team B": {"price": 3.00, "bookmaker": "bookmaker2"}
        }
      }
    }]
  }
}
```

## 🧪 Testing

### Run Tests
```bash
# Complete test suite
pytest tests/ -v

# Test categories
pytest tests/ -m unit -v        # Unit tests
pytest tests/ -m integration -v # Integration tests  
pytest tests/ -m arbitrage -v   # Arbitrage detection
pytest tests/ -m parallel -v    # Parallel processing

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### Test Structure
- **Unit tests**: Individual component testing
- **Integration tests**: Complete workflow testing
- **Performance tests**: Load and stress testing
- **API tests**: Endpoint validation

## 🏀 Supported Sports

**US Major Sports (Primary):**
- NBA, WNBA, NFL, MLB, NHL, MLS

**International Sports (40+):**
- Premier League, La Liga, Bundesliga, Serie A
- UFC, Boxing, Cricket, Rugby
- Golf, Tennis, and more

Full list available at `/api/enhanced/sports`

## ⚡ Performance

- **API Response**: <200ms single sport
- **Multi-Sport**: <1000ms for 10 sports  
- **Accuracy**: 95%+ arbitrage detection
- **Test Coverage**: 90%+ code coverage
- **Profit Detection**: 21%+ in test scenarios

## 🌐 California Offshore Focus

**Supported Platforms:**
- ✅ BetOnline.ag, Bovada, BetUS (legal for CA residents)
- ❌ FanDuel, DraftKings (not legal in CA)

**Compliance Features:**
- Educational market analysis focus
- Offshore platform specialization
- Risk disclosure and warnings

## 📚 Documentation

- **[API Guide](API_GUIDE.md)**: Complete API testing and usage
- **[Product Specs](PRODUCT_SPECIFICATION.md)**: Detailed requirements
- **Interactive Docs**: `http://localhost:8000/docs`

## 🤝 Contributing

1. Fork repository
2. Create feature branch  
3. Add comprehensive tests
4. Submit pull request

## 📞 Contact

- **GitHub**: [AKarode](https://github.com/AKarode)
- **Issues**: GitHub Issues for bugs/features
- **Business**: Focus on California offshore markets

---

<div align="center">

**Built for California arbitrage traders • AI-powered market analysis**

</div>