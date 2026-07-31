from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.api_config import router as config_router
from api.api_regime import router as regime_router

# Create FastAPI application
app = FastAPI(
    title="Technical Analysis Helper API",
    description="API for technical analysis and trading signals",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(config_router)
app.include_router(regime_router)

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Welcome to Technical Analysis Helper API",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/regime/0-stats",
            "/regime/pull-history",
            "/regime/check-continuity",
            "/regime/pipeline",
            "/regime/1-label",
            "/regime/2-train",
            "/regime/3-predict",
            "/regime/explain-rules",
            "/config",
        ]
    }

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}
