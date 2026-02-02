from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.api_fetch_okex import router as fetch_router

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
app.include_router(fetch_router)

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Welcome to Technical Analysis Helper API",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/api/features",
            "/api/prediction",
            "/fetch/okex"
        ]
    }

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Sample features endpoint
@app.get("/api/features")
def get_features():
    """Get sample features data"""
    return {
        "features": {
            "close_1h_normalized": 0.123,
            "volume_1h_normalized": 0.456,
            "rsi_14_1h": 55.5,
            "macd_line_1h": 0.001,
            "macd_signal_1h": 0.0005
        },
        "timestamp": 1769130000000
    }

# Sample prediction endpoint
@app.get("/api/prediction")
def get_prediction():
    """Get sample prediction"""
    return {
        "prediction": {
            "predicted_class": 1,
            "confidence": 0.75,
            "prediction_description": "Very light bullish movement (0.5% to 1.0%)"
        },
        "timestamp": 1769130000000
    }
