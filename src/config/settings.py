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
    
    # Redis Configuration
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB = int(os.getenv('REDIS_DB', '1'))
    REDIS_SIGNAL_STREAM = os.getenv('REDIS_SIGNAL_STREAM', 'signals')
    
    # MongoDB Configuration
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'technical_analysis')
    
    # MongoDB Collections
    MONGODB_COLLECTIONS = {
        'candlesticks': os.getenv('MONGODB_CANDLESTICKS_COLLECTION', 'candlesticks'),
        'features': os.getenv('MONGODB_FEATURES_COLLECTION', 'features'),
        'features_prediction': os.getenv('MONGODB_FEATURES_PREDICTION_COLLECTION', 'features_prediction'),
        'normalizer': os.getenv('MONGODB_NORMALIZER_COLLECTION', 'normalizer'),
        'config': os.getenv('MONGODB_CONFIG_COLLECTION', 'config')
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
    MODEL_SAVE_PATH_LOW = os.getenv('MODEL_SAVE_PATH_LOW', 'models/xgboost_model_low.json')
    MODEL_SAVE_PATH_HIGH = os.getenv('MODEL_SAVE_PATH_HIGH', 'models/xgboost_model_high.json')
    FEATURE_WINDOW_SIZE = int(os.getenv('FEATURE_WINDOW_SIZE', '300'))
    
    # Time windows for technical indicators (in hours)
    TIME_WINDOWS = {
        'short': 12,     # 12 hours
        'medium': 48,    # 2 days (48 hours)
        'long': 192      # 8 days (192 hours)
    }
    
    # Price movement classification thresholds (in percentage)
    CLASSIFICATION_THRESHOLDS = {   
        1: (-100, -3.6),     # 暴跌
        2: (-3.6, -1.2),     # 下跌
        3: (-1.2, 1.2),      # 横盘
        4: (1.2, 3.6),       # 上涨
        5: (3.6, 100),       # 暴涨    
    }
    
    CLASSIFICATION_THRESHOLDS_DESC = {   
        1: "暴跌 (<-3.6%)",     # 暴跌
        2: "下跌 (-3.6% ~ -1.2%)",     # 下跌
        3: "横盘 (-1.2% ~ 1.2%)",      # 横盘
        4: "上涨 (1.2% ~ 3.6%)",       # 上涨
        5: "暴涨 (>3.6%)",       # 暴涨    
    }
    
    CLASSIFICATION_THRESHOLDS_HIGH = {   
        1: (-100, 1.2),      # 没涨
        2: (1.2, 3.6),        # 上涨
        3: (3.6, 100),        # 暴涨
    }
    
    CLASSIFICATION_THRESHOLDS_HIGH_DESC = {
        1: "没涨 (<1.2%)",      # 没涨
        2: "上涨 (1.2% ~ 3.6%)",        # 上涨
        3: "超涨 (>3.6%)",        # 暴涨
    }
    
    CLASSIFICATION_THRESHOLDS_LOW = {   
        1: (-100, -3.6),      # 暴跌
        2: (-3.6, -1.2),      # 下跌
        3: (1.2, 100),       # 没跌
    }
    
    CLASSIFICATION_THRESHOLDS_LOW_DESC = {
        1: "暴跌 (<-3.6%)",     # 暴跌
        2: "下跌 (-3.6% ~ -1.2%)",     # 下跌
        3: "没跌 (<1.2%)",      # 横盘
    }
    
    # Environment Mode
    # 默认是false，开发环境
    PRODUCTION_MODE = os.getenv('PRODUCTION_MODE', 'false').lower() == 'true'
    
    # Scheduled Task Configuration
    SCHEDULE_ENABLED = os.getenv('SCHEDULE_ENABLED', 'false').lower() == 'true'
    SCHEDULE_INTERVAL = int(os.getenv('SCHEDULE_INTERVAL', '1'))  # minutes
    SCHEDULE_RECIPIENT = os.getenv('SCHEDULE_RECIPIENT', '284160266@qq.com')
    SCHEDULE_DATA_SOURCE = os.getenv('SCHEDULE_DATA_SOURCE', 'mongodb')  # 'mongodb' or 'api'

# Create a global config instance
config = Config()