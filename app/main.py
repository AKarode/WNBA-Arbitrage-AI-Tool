from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import API routers
from app.api.odds import router as odds_router
from app.api.multi_source_odds import router as multi_source_odds_router

app = FastAPI(
    title="WNBA Arbitrage AI Tool",
    description="AI-powered arbitrage betting tool for WNBA games",
    version="1.0.0",
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

@app.get("/")
async def root():
    return {"message": "WNBA Arbitrage AI Tool API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 