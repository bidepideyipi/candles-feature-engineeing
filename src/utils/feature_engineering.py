"""
Feature engineering pipeline for creating training datasets.
"""

import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

from ..utils.technical_indicators import tech_calculator
from ..config.settings import config

logger = logging.getLogger(__name__)

class FeatureEngineer:
    """Creates features from raw candlestick data for machine learning."""
    
    def __init__(self):
        """Initialize feature engineer."""
        self.feature_window_size = config.FEATURE_WINDOW_SIZE
    
    def create_features_from_data(self, data: List[Dict[str, Any]], 
                                prediction_horizon: int = 24) -> Optional[Dict[str, Any]]:
        """
        Create features from candlestick data for a single prediction point.
        
        Args:
            data: List of candlestick data dictionaries
            prediction_horizon: Number of periods to look ahead for return calculation
            
        Returns:
            Dictionary containing features and target, or None if insufficient data
        """
        if len(data) < self.feature_window_size + prediction_horizon:
            logger.warning(f"Insufficient data. Need {self.feature_window_size + prediction_horizon} records, got {len(data)}")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Take the last feature_window_size + prediction_horizon records
        # The last prediction_horizon records are used for calculating future return
        sample_df = df.tail(self.feature_window_size + prediction_horizon).copy()
        
        # Separate current data (for features) and future data (for target)
        current_data = sample_df.head(self.feature_window_size)
        future_data = sample_df.tail(prediction_horizon + 1)
        
        # Calculate technical indicators
        indicators = tech_calculator.calculate_indicators(current_data)
        
        # Calculate price features (including future return)
        price_features = tech_calculator.calculate_price_features(
            pd.concat([current_data, future_data]), 
            prediction_horizon
        )
        
        if price_features.get('classification_label') is None:
            logger.warning("Could not calculate classification label")
            return None
        
        # Combine all features
        features = {}
        features.update(indicators)
        features.update(price_features)
        
        # Add timestamp for reference
        features['timestamp'] = int(current_data['timestamp'].iloc[-1])
        
        return features
    
    def create_training_dataset(self, data: List[Dict[str, Any]], 
                              stride: int = 1,
                              prediction_horizon: int = 24) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Create training dataset from historical data.
        
        Args:
            data: List of candlestick data dictionaries
            stride: Number of periods to skip between samples
            prediction_horizon: Number of periods to look ahead for return calculation
            
        Returns:
            Tuple of (features DataFrame, target Series)
        """
        logger.info(f"Creating training dataset from {len(data)} records")
        logger.info(f"Parameters: stride={stride}, prediction_horizon={prediction_horizon}")
        
        features_list = []
        targets_list = []
        
        # Start from the beginning, create overlapping windows
        start_idx = 0
        while start_idx + self.feature_window_size + prediction_horizon <= len(data):
            end_idx = start_idx + self.feature_window_size
            
            # Extract window data
            window_data = data[start_idx:end_idx + prediction_horizon]
            
            # Create features for this window
            features_dict = self.create_features_from_data(window_data, prediction_horizon)
            
            if features_dict:
                target = features_dict.pop('classification_label')
                timestamp = features_dict.pop('timestamp')
                
                features_list.append(features_dict)
                targets_list.append(target)
            
            start_idx += stride
        
        if not features_list:
            logger.error("No valid samples created for training dataset")
            return pd.DataFrame(), pd.Series(dtype=int)
        
        # Create DataFrame
        features_df = pd.DataFrame(features_list)
        targets_series = pd.Series(targets_list, name='target')
        
        logger.info(f"Created training dataset with {len(features_df)} samples")
        logger.info(f"Target distribution: {targets_series.value_counts().to_dict()}")
        
        return features_df, targets_series
    
    def prepare_prediction_features(self, data: List[Dict[str, Any]]) -> Optional[pd.DataFrame]:
        """
        Prepare features for making predictions on current data.
        
        Args:
            data: List of recent candlestick data
            
        Returns:
            DataFrame with features for prediction, or None if insufficient data
        """
        if len(data) < self.feature_window_size:
            logger.warning(f"Insufficient data for prediction. Need {self.feature_window_size}, got {len(data)}")
            return None
        
        # Take the most recent data
        recent_data = data[-self.feature_window_size:]
        
        # Convert to DataFrame
        df = pd.DataFrame(recent_data)
        
        # Calculate technical indicators
        indicators = tech_calculator.calculate_indicators(df)
        
        # Calculate current price features (without future return)
        price_features = {
            'current_price': float(df['close'].iloc[-1]),
            'price_volatility': float(df['close'].tail(24).std() / df['close'].tail(24).mean()),
            'volume_avg': float(df['volume'].tail(24).mean()),
            'price_trend_24h': float((df['close'].iloc[-1] / df['close'].iloc[-25] - 1) * 100) if len(df) >= 25 else np.nan
        }
        
        # Combine features
        features = {}
        features.update(indicators)
        features.update(price_features)
        
        # Return as DataFrame
        return pd.DataFrame([features])

# Global instance
feature_engineer = FeatureEngineer()