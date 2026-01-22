"""
Feature dataset builder for creating training datasets from historical data.
"""

import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple

from ..config.settings import config
from .technical_indicators import tech_calculator
from .label_generator import label_generator

logger = logging.getLogger(__name__)

class FeatureDatasetBuilder:
    """
    Builds training datasets from historical OHLCV data.
    Combines technical indicators and price features.
    """
    
    def __init__(self):
        """
        Initialize feature dataset builder.
        """
        self.feature_window_size = config.FEATURE_WINDOW_SIZE
        self.time_windows = config.TIME_WINDOWS
    
    def create_training_dataset(self, data: List[Dict[str, Any]], stride: int = 10, prediction_horizon: int = 24) -> Tuple[pd.DataFrame, pd.Series]:
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
        
        if len(data) < self.feature_window_size + prediction_horizon:
            logger.error(f"Insufficient data. Need {self.feature_window_size + prediction_horizon} records, got {len(data)}")
            return pd.DataFrame(), pd.Series(dtype=int)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        features_list = []
        targets_list = []
        
        # Create sliding windows
        start_idx = 0
        while start_idx + self.feature_window_size + prediction_horizon <= len(df):
            # Extract window data
            window_end = start_idx + self.feature_window_size
            future_end = window_end + prediction_horizon
            
            window_data = df.iloc[start_idx:window_end].copy()
            future_data = df.iloc[window_end:future_end].copy()
            
            # Calculate features
            features = self._extract_features(window_data, future_data, prediction_horizon)
            
            if features and 'classification_label' in features:
                target = features.pop('classification_label')
                features_list.append(features)
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
    
    def _extract_features(self, current_data: pd.DataFrame, future_data: pd.DataFrame, prediction_horizon: int) -> Dict[str, Any]:
        """
        Extract features from current and future data.
        
        Args:
            current_data: DataFrame with current period data (for features)
            future_data: DataFrame with future period data (for target)
            prediction_horizon: Number of periods to look ahead
            
        Returns:
            Dictionary of features including target label
        """
        features = {}
        
        # Calculate technical indicators
        indicators = tech_calculator.calculate_indicators(current_data)
        features.update(indicators)
        
        # Calculate price features including future return
        combined_data = pd.concat([current_data, future_data])
        price_features = tech_calculator.calculate_price_features(combined_data, prediction_horizon)
        
        if 'classification_label' not in price_features:
            logger.warning("Could not calculate classification label")
            return {}
        
        features.update(price_features)
        
        # Add timestamp for reference
        features['timestamp'] = int(current_data['timestamp'].iloc[-1])
        
        # Extract raw price series features
        raw_features = self._extract_raw_price_features(current_data)
        features.update(raw_features)
        
        return features
    
    def _extract_raw_price_features(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract raw price series features to preserve time series information.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary of raw price features
        """
        if len(df) < self.feature_window_size:
            logger.warning(f"Insufficient data for raw price extraction. Need {self.feature_window_size}, got {len(df)}")
            return {}
        
        # Ensure we have exactly feature_window_size records
        window_df = df.tail(self.feature_window_size).copy()
        
        raw_features = {}
        
        # Recent price levels (most recent first)
        for i in range(min(24, len(window_df))):  # Last 24 hours
            idx = -(i + 1)
            raw_features[f'raw_close_{i+1}h'] = float(window_df['close'].iloc[idx])
            raw_features[f'raw_high_{i+1}h'] = float(window_df['high'].iloc[idx])
            raw_features[f'raw_low_{i+1}h'] = float(window_df['low'].iloc[idx])
            raw_features[f'raw_volume_{i+1}h'] = float(window_df['volume'].iloc[idx])
        
        # Statistical features from raw data
        raw_features['raw_price_mean'] = float(window_df['close'].mean())
        raw_features['raw_price_std'] = float(window_df['close'].std())
        raw_features['raw_price_min'] = float(window_df['close'].min())
        raw_features['raw_price_max'] = float(window_df['close'].max())
        
        # Price changes
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
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Use most recent data for features
        recent_data = df.tail(self.feature_window_size).copy()
        
        # Calculate features
        indicators = tech_calculator.calculate_indicators(recent_data)
        
        # Calculate current price features
        price_features = {
            'current_price': float(recent_data['close'].iloc[-1]),
            'price_volatility': float(recent_data['close'].tail(24).std() / recent_data['close'].tail(24).mean()),
            'volume_avg': float(recent_data['volume'].tail(24).mean()),
            'price_trend_24h': float((recent_data['close'].iloc[-1] / recent_data['close'].iloc[-25] - 1) * 100) if len(recent_data) >= 25 else np.nan
        }
        
        # Combine features
        features = {}
        features.update(indicators)
        features.update(price_features)
        
        # Return as DataFrame
        return pd.DataFrame([features])

# Global instance
feature_engineer = FeatureDatasetBuilder()