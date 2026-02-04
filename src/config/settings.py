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
    
    # MongoDB Collections
    MONGODB_COLLECTIONS = {
        'candlesticks': os.getenv('MONGODB_CANDLESTICKS_COLLECTION', 'candlesticks'),
        'features': os.getenv('MONGODB_FEATURES_COLLECTION', 'features'),
        'normalizer': os.getenv('MONGODB_NORMALIZER_COLLECTION', 'normalizer')
    }
    
    # Backward compatibility - default collection
    MONGODB_COLLECTION = MONGODB_COLLECTIONS['candlesticks']
    
    # Redis Configuration
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB = int(os.getenv('REDIS_DB', '1'))
    
    # OKEx API Configuration
    OKEX_API_BASE_URL = os.getenv('OKEX_API_BASE_URL', 'https://www.okx.com')
    
    # Model Configuration
    MODEL_SAVE_PATH = os.getenv('MODEL_SAVE_PATH', 'models/xgboost_model.json')
    FEATURE_WINDOW_SIZE = int(os.getenv('FEATURE_WINDOW_SIZE', '300'))
    
    # Time windows for technical indicators (in hours)
    TIME_WINDOWS = {
        'short': 12,     # 12 hours
        'medium': 48,    # 2 days (48 hours)
        'long': 192      # 8 days (192 hours)
    }
    
    # Price movement classification thresholds (in percentage)
    CLASSIFICATION_THRESHOLDS = {   
        1: (-100, -1.2),    
        2: (-1.2, 1.2),     
        3: (1.2, 100),       
    }

# Create a global config instance
config = Config()