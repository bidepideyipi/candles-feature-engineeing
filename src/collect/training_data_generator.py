"""
Training data generator that orchestrates data fetching, storage, and feature creation.
"""

import logging
import os
from typing import Tuple, Optional
import pandas as pd

from ..collect.mongodb_handler import mongo_handler
from ..feature.feature_engineering import feature_engineer
from ..config.settings import config

logger = logging.getLogger(__name__)

class TrainingDataGenerator:
    """Generates training datasets by fetching data, storing it, and creating features."""
    
    def __init__(self):
        """Initialize training data generator."""
        self.feature_window_size = config.FEATURE_WINDOW_SIZE
    
    def generate_training_data(self, 
                             max_records: int = 50000,
                             stride: int = 10,
                             prediction_horizon: int = 24) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Complete pipeline to generate training data.
        
        Args:
            max_records: Maximum number of historical records to fetch
            stride: Stride between training samples
            prediction_horizon: Prediction horizon in hours
            
        Returns:
            Tuple of (features DataFrame, targets Series)
        """
        logger.info("Starting training data generation pipeline")
        
        # Import here to avoid circular import
        from ..collect.okex_fetcher import okex_fetcher
        
        # Step 1: Fetch historical data
        logger.info("Step 1: Fetching historical data from OKEx API")
        historical_data = okex_fetcher.fetch_historical_data(max_records=max_records)
        
        if not historical_data:
            logger.error("Failed to fetch historical data")
            return pd.DataFrame(), pd.Series(dtype=int)
        
        logger.info(f"Fetched {len(historical_data)} historical records")
        
        # Step 2: Store data in MongoDB
        logger.info("Step 2: Storing data in MongoDB")
        if not mongo_handler.insert_candlestick_data(historical_data):
            logger.warning("Failed to store some data in MongoDB, continuing...")
        
        # Step 3: Create training dataset
        logger.info("Step 3: Creating training dataset with features")
        features_df, targets_series = feature_engineer.create_training_dataset(
            historical_data, 
            stride=stride,
            prediction_horizon=prediction_horizon
        )
        
        if features_df.empty:
            logger.error("Failed to create training dataset")
            return pd.DataFrame(), pd.Series(dtype=int)
        
        # Log dataset statistics
        self._log_dataset_statistics(features_df, targets_series)
        
        logger.info("Training data generation completed successfully")
        return features_df, targets_series
    
    """
    从Mongodb加载已经存在的基础数据转为DataFrame格式
    """
    def load_existing_training_data(self, 
                                  inst_id :str = "ETH-USDT-SWAP",
                                  stride: int = 10,
                                  prediction_horizon: int = 24) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Load training data from existing MongoDB records.
        
        Args:
            inst_id: Instrument ID to filter by (e.g., "ETH-USDT-SWAP")
            stride: Stride between training samples
            prediction_horizon: Prediction horizon in hours
            
        Returns:
            Tuple of (features DataFrame, targets Series)
        """
        logger.info("Loading training data from MongoDB")
        
        # Fetch data from MongoDB (default to ETH-USDT-SWAP)
        db_data = mongo_handler.get_candlestick_data(limit=10000, inst_id=inst_id)
        
        if not db_data:
            logger.error("No data found in MongoDB")
            return pd.DataFrame(), pd.Series(dtype=int)
        
        # Convert MongoDB documents to the expected format
        candlestick_data = []
        for doc in db_data:
            candlestick_data.append({
                'timestamp': doc['timestamp'],
                'open': doc['open'],
                'high': doc['high'],
                'low': doc['low'],
                'close': doc['close'],
                'volume': doc['volume'],
                'vol_ccy': doc.get('vol_ccy', 0),
                'vol_ccy_quote': doc.get('vol_ccy_quote', 0),
                'confirm': doc.get('confirm', 1)
            })
        
        logger.info(f"Loaded {len(candlestick_data)} records from MongoDB")
        
        # Create training dataset
        features_df, targets_series = feature_engineer.create_training_dataset(
            candlestick_data,
            stride=stride,
            prediction_horizon=prediction_horizon
        )
        
        if features_df.empty:
            logger.error("Failed to create training dataset from MongoDB data")
            return pd.DataFrame(), pd.Series(dtype=int)
        
        self._log_dataset_statistics(features_df, targets_series)
        
        return features_df, targets_series
    
    def _log_dataset_statistics(self, features_df: pd.DataFrame, targets_series: pd.Series):
        """Log statistics about the generated dataset."""
        logger.info("=" * 50)
        logger.info("DATASET STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Number of samples: {len(features_df)}")
        logger.info(f"Number of features: {len(features_df.columns)}")
        logger.info(f"Feature columns: {list(features_df.columns)}")
        logger.info(f"Target distribution:")
        for label, count in targets_series.value_counts().sort_index().items():
            percentage = (count / len(targets_series)) * 100
            logger.info(f"  Class {label}: {count} samples ({percentage:.2f}%)")
        logger.info("=" * 50)
        
        # Check for missing values
        missing_values = features_df.isnull().sum()
        if missing_values.any():
            logger.warning("Features with missing values:")
            for col, count in missing_values[missing_values > 0].items():
                logger.warning(f"  {col}: {count} missing values")

# Global instance
training_generator = TrainingDataGenerator()