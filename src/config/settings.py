"""
Configuration module for the technical analysis helper project.
Handles loading environment variables and providing configuration values.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class containing all project settings."""
    
    # MongoDB Configuration
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'technical_analysis')
    MONGODB_COLLECTION = os.getenv('MONGODB_COLLECTION', 'candlesticks')
    
    # Redis Configuration
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB = int(os.getenv('REDIS_DB', '1'))
    
    # OKEx API Configuration
    OKEX_API_BASE_URL = os.getenv('OKEX_API_BASE_URL', 'https://www.okx.com')
    INST_ID = os.getenv('INST_ID', 'ETH-USDT-SWAP')
    
    # Model Configuration
    MODEL_SAVE_PATH = os.getenv('MODEL_SAVE_PATH', 'models/xgboost_model.json')
    FEATURE_WINDOW_SIZE = int(os.getenv('FEATURE_WINDOW_SIZE', '300'))
    
    # Time windows for technical indicators (in hours)
    TIME_WINDOWS = {
        'short': 24,    # 24 hours
        'medium': 72,   # 3 days (72 hours)
        'long': 168     # 1 week (168 hours)
    }
    
    # Price movement classification thresholds (in percentage)
    CLASSIFICATION_THRESHOLDS = {
        -3: (-100, -5.5),    # <-5.5%
        -2: (-5.5, -2.5),    # -2.5% to -5.0%
        -1: (-2.5, -0.5),    # -0.5% to -2.5%
        0: (-0.5, 0.5),      # -0.5% to 0.5%
        1: (0.5, 2.5),       # 0.5% to 2.5%
        2: (2.5, 5.5),       # 2.5% to 5.5%
        3: (5.5, 100)        # >5.5%
    }

# Create a global config instance
config = Config()