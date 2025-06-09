from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import API routers
from core.api.odds import router as odds_router
from core.api.multi_source_odds import router as multi_source_odds_router
from core.api.enhanced_arbitrage import router as enhanced_arbitrage_router

app = FastAPI(
    title="Enhanced Sports Arbitrage Detection System",
    description="""
    AI-powered arbitrage detection system with advanced capabilities:
    
    🚀 **Enhanced Features:**
    - 47+ sports coverage with parallel processing
    - Cross-market arbitrage detection (moneyline, spreads, totals)
    - Real-time optimization and California offshore focus
    - Advanced risk assessment and confidence scoring
    - Performance monitoring and dynamic configuration
    
    📊 **Supported Markets:**
    - Moneyline (h2h) arbitrage
    - Point spread arbitrage  
    - Totals (over/under) arbitrage
    - Cross-market opportunities
    
    🎯 **California Offshore Sportsbooks:**
    - BetOnline.ag, Bovada, BetUS, LowVig.ag
    - MyBookie, Heritage Sports integration
    
    Use `/api/enhanced/` endpoints for advanced features.
    """,
    version="2.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(odds_router)
app.include_router(multi_source_odds_router)
app.include_router(enhanced_arbitrage_router)

@app.get("/")
async def root():
    return {"message": "Sports Arbitrage Detection System API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/sports")
async def get_supported_sports():
    """Get list of all supported sports for arbitrage detection"""
    return {
        "supported_sports": [
            {"key": "basketball_nba", "title": "NBA", "active": True},
            {"key": "basketball_wnba", "title": "WNBA", "active": True},
            {"key": "americanfootball_nfl", "title": "NFL", "active": True},
            {"key": "baseball_mlb", "title": "MLB", "active": True},
            {"key": "icehockey_nhl", "title": "NHL", "active": True},
            {"key": "soccer_usa_mls", "title": "MLS", "active": True}
        ],
        "total": 6
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)