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
        Preserves both technical indicators AND raw price series data.
        
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
        
        # Preserve raw price series data (the core time series information)
        raw_price_features = self._extract_raw_price_series(current_data)
        
        # Combine all features
        features = {}
        features.update(indicators)        # Technical indicators as辅助 features
        features.update(price_features)   # Derived price metrics
        features.update(raw_price_features)  # Raw price series (核心数据)
        
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
                
                # Add timestamp back to features for reference
                features_dict['timestamp'] = timestamp
                
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
    
    def _extract_raw_price_series(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract raw price series data to preserve original time series information.
        This preserves the essential OHLCV data that technical indicators are derived from.
        
        Args:
            df: DataFrame with OHLCV data for the feature window
            
        Returns:
            Dictionary containing raw price series features
        """
        if len(df) < self.feature_window_size:
            logger.warning(f"Insufficient data for raw price extraction. Need {self.feature_window_size}, got {len(df)}")
            return {}
        
        # Ensure we have exactly feature_window_size records
        window_df = df.tail(self.feature_window_size).copy()
        
        # Extract raw price series (these are the fundamental inputs)
        raw_features = {}
        
        # Recent price levels (most recent first)
        for i in range(min(24, len(window_df))):  # Last 24 hours
            idx = -(i + 1)
            raw_features[f'raw_close_{i+1}h'] = float(window_df['close'].iloc[idx])
            raw_features[f'raw_high_{i+1}h'] = float(window_df['high'].iloc[idx])
            raw_features[f'raw_low_{i+1}h'] = float(window_df['low'].iloc[idx])
            raw_features[f'raw_open_{i+1}h'] = float(window_df['open'].iloc[idx])
            raw_features[f'raw_volume_{i+1}h'] = float(window_df['volume'].iloc[idx])
        
        # Statistical features from raw data
        raw_features['raw_price_mean'] = float(window_df['close'].mean())
        raw_features['raw_price_std'] = float(window_df['close'].std())
        raw_features['raw_price_min'] = float(window_df['close'].min())
        raw_features['raw_price_max'] = float(window_df['close'].max())
        
        # Price changes (原始价格变化)
        price_changes = window_df['close'].diff().dropna()
        if len(price_changes) > 0:
            raw_features['raw_price_change_mean'] = float(price_changes.mean())
            raw_features['raw_price_change_std'] = float(price_changes.std())
            raw_features['raw_price_change_sum'] = float(price_changes.sum())
        
        # Volume features
        raw_features['raw_volume_mean'] = float(window_df['volume'].mean())
        raw_features['raw_volume_std'] = float(window_df['volume'].std())
        
        # Price range features
        raw_features['raw_price_range_mean'] = float((window_df['high'] - window_df['low']).mean())
        raw_features['raw_price_range_max'] = float((window_df['high'] - window_df['low']).max())
        
        logger.debug(f"Extracted {len(raw_features)} raw price series features")
        return raw_features

# Global instance
feature_engineer = FeatureEngineer()