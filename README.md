# WNBA Arbitrage AI Tool

An AI-powered arbitrage betting tool focused on WNBA games for California users, targeting offshore sportsbooks.

## 🎯 Project Overview

- **Goal**: Detect profitable arbitrage opportunities in WNBA betting markets
- **Timeline**: 8-10 weeks to MVP
- **Testing Period**: WNBA 2025 season (May-October)
- **Target Users**: California sports bettors using offshore sportsbooks

## 🏗️ Technical Architecture

### Core Components
1. **Data Collection Engine** - Gather odds, news, and game data
2. **Traditional ML Models** - Line prediction and arbitrage detection
3. **LLM Integration** - News analysis and strategic advice
4. **Web Dashboard** - User interface and alerts
5. **Database Layer** - Data storage and management
6. **Alert System** - Real-time notifications

### Tech Stack
- **Backend**: Python (FastAPI)
- **Frontend**: React/Next.js
- **Database**: PostgreSQL + Redis
- **ML**: scikit-learn, XGBoost, TensorFlow
- **LLM**: OpenAI API / Anthropic Claude
- **Deployment**: Docker + AWS/Railway

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend development)
- PostgreSQL (for database)
- Redis (for caching)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd wnba-arbitrage-tool
```

2. Set up Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp env_template.txt .env
# Edit .env with your actual API keys and configuration
```

5. Run the development server:
```bash
python app/main.py
```

The API will be available at `http://localhost:8000`

## 📁 Project Structure

```
wnba-arbitrage-tool/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── api/                 # API endpoints
│   ├── database/            # Database models and connections
│   ├── models/              # Pydantic models
│   └── services/            # Business logic
├── tests/                   # Unit and integration tests
├── requirements.txt         # Python dependencies
├── env_template.txt         # Environment variables template
└── README.md               # This file
```

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app
```

## 📈 Development Phases

- **Phase 1**: Foundation (Weeks 1-3) - Data collection and basic infrastructure
- **Phase 2**: ML Models (Weeks 4-5) - Traditional ML and LLM integration
- **Phase 3**: User Interface (Weeks 6-7) - Web dashboard and alerts  
- **Phase 4**: Testing & Deployment (Weeks 8-10) - Production deployment

## 🔧 Configuration

Edit `.env` file with your API keys:
- The Odds API key for sports betting data
- OpenAI/Anthropic API keys for LLM features
- Database connection strings
- Email/SMS service credentials

## 📝 License

This project is for educational and research purposes only. Please gamble responsibly and be aware of local laws regarding sports betting.

---

**Status**: Day 1 Complete - Basic project structure and environment set up ✅ 