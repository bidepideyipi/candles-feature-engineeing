"""
Feature Engineering Module
Implements the modular assembly pattern for technical indicator calculation
following the architecture documented in docs/architecture.md lines 194-233
"""

import logging
import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, Any
from datetime import datetime

from collect.candlestick_handler import candlestick_handler
from collect.normalization_handler import normalization_handler
from config.settings import config

# Import calculator modules
from utils.rsi_calculator import RSICalculator
from utils.macd_calculator import MACDCalculator
from utils.normalize_encoder import Normalized
from utils.impulse_calculator import ImpulseCalculator
from utils.trend_continuation_calulator import TrendContinuationCalculator
from utils.time_encoder import TimestampEncoder 

logger = logging.getLogger(__name__)

class FeatureEngineer:
    """Orchestrates feature engineering following the modular assembly pattern."""
    
    def __init__(self):
        """Initialize FeatureEngineer with required handlers and calculators."""
        logger.info("Initializing FeatureEngineer")
        
        # Initialize calculators
        self.rsi_calc = RSICalculator()
        self.macd_calc = MACDCalculator()
        self.norm_calc = Normalized()
        self.impulse_calc = ImpulseCalculator()
        self.trend_calc = TrendContinuationCalculator()
        self.time_calc = TimestampEncoder()
        
        # Time windows for different granularities
        self.time_windows = {
            '1H': 14,    # 14 periods for 1-hour data
            '15m': 14,   # 14 periods for 15-minute data  
            '4H': 14     # 14 periods for 4-hour data
        }
    
    def create_training_dataset(self, raw_data: list, stride: int = 10, 
                              prediction_horizon: int = 24) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Create training dataset following the architecture flow.
        
        Args:
            raw_data: Raw candlestick data from MongoDB
            stride: Sliding window stride
            prediction_horizon: Hours ahead for prediction
            
        Returns:
            Tuple of (features DataFrame, targets Series)
        """
        logger.info("Creating training dataset")
        
        # Convert raw data to DataFrame
        df = self._convert_to_dataframe(raw_data)
        if df.empty:
            logger.error("Empty data provided")
            return pd.DataFrame(), pd.Series()
        
        # Get normalization parameters
        norm_params = self._get_normalization_parameters()
        
        # Process data by time dimensions
        features_list = []
        targets_list = []
        
        # Sliding window processing
        for i in range(0, len(df) - prediction_horizon, stride):
            if i + config.FEATURE_WINDOW_SIZE + prediction_horizon > len(df):
                break
                
            window_data = df.iloc[i:i + config.FEATURE_WINDOW_SIZE]
            future_data = df.iloc[i + config.FEATURE_WINDOW_SIZE:i + config.FEATURE_WINDOW_SIZE + prediction_horizon]
            
            # Extract features for this window
            features = self._extract_features(window_data, norm_params)
            if features:
                features_list.append(features)
                
                # Generate target (future price movement)
                target = self._generate_target(window_data.iloc[-1], future_data)
                targets_list.append(target)
        
        if not features_list:
            logger.error("No features extracted")
            return pd.DataFrame(), pd.Series()
        
        # Convert to DataFrame
        features_df = pd.DataFrame(features_list)
        targets_series = pd.Series(targets_list)
        
        logger.info(f"Created dataset with {len(features_df)} samples and {len(features_df.columns)} features")
        return features_df, targets_series
    
    def prepare_prediction_features(self, raw_data: list) -> Optional[pd.DataFrame]:
        """
        Prepare features for prediction on latest data.
        
        Args:
            raw_data: Recent candlestick data
            
        Returns:
            DataFrame with features for prediction, or None if failed
        """
        logger.info("Preparing prediction features")
        
        # Convert raw data to DataFrame
        df = self._convert_to_dataframe(raw_data)
        if df.empty or len(df) < config.FEATURE_WINDOW_SIZE:
            logger.error("Insufficient data for prediction")
            return None
        
        # Get most recent window
        recent_data = df.tail(config.FEATURE_WINDOW_SIZE)
        
        # Get normalization parameters
        norm_params = self._get_normalization_parameters()
        
        # Extract features
        features = self._extract_features(recent_data, norm_params)
        if not features:
            logger.error("Failed to extract features for prediction")
            return None
        
        return pd.DataFrame([features])
    
    def _convert_to_dataframe(self, raw_data: list) -> pd.DataFrame:
        """Convert raw MongoDB data to pandas DataFrame."""
        if not raw_data:
            return pd.DataFrame()
        
        try:
            df = pd.DataFrame(raw_data)
            # Convert timestamp to datetime if needed
            if 'timestamp' in df.columns:
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                df = df.sort_values('timestamp').reset_index(drop=True)
            return df
        except Exception as e:
            logger.error(f"Failed to convert data to DataFrame: {e}")
            return pd.DataFrame()
    
    def _get_normalization_parameters(self) -> Dict[str, Dict[str, float]]:
        """
        Get normalization parameters from normalization_handler.
        This corresponds to step B1 in the architecture flowchart.
        """
        norm_params = {}
        
        # Get parameters for close prices
        close_params = normalization_handler.get_normalization_params(
            inst_id="ETH-USDT-SWAP", 
            bar="1H", 
            column="close"
        )
        if close_params:
            norm_params['close'] = close_params
        
        # Get parameters for volume
        volume_params = normalization_handler.get_normalization_params(
            inst_id="ETH-USDT-SWAP", 
            bar="1H", 
            column="volume"
        )
        if volume_params:
            norm_params['volume'] = volume_params
            
        logger.info(f"Retrieved normalization parameters for {len(norm_params)} columns")
        return norm_params
    
    def _extract_features(self, df: pd.DataFrame, norm_params: Dict) -> Optional[Dict[str, Any]]:
        """
        Extract features following the modular assembly pattern.
        This implements the core algorithm flow from the architecture diagram.
        """
        if df.empty:
            return None
        
        features = {}
        
        try:
            # 1. Process 1-hour data (corresponds to branch D in flowchart)
            if len(df) >= self.time_windows['1H']:
                hourly_data = df[df['bar'] == '1H'] if 'bar' in df.columns else df
                if len(hourly_data) >= self.time_windows['1H']:
                    # Call RSI calculator
                    rsi_14_1h = self.rsi_calc.get_last_value(hourly_data['close'].tail(self.time_windows['1H']))
                    features['rsi_14_1h'] = rsi_14_1h
                    
                    # Call MACD calculator
                    macd_line, macd_signal, _ = self.macd_calc.get_last_values(hourly_data['close'].tail(50))
                    features['macd_line_1h'] = macd_line
                    features['macd_signal_1h'] = macd_signal
                    
                    # Call normalization encoder for close prices
                    if 'close' in norm_params:
                        close_norm = self.norm_calc.calculate(
                            hourly_data['close'].tail(self.time_windows['1H']),
                            norm_params['close']['mean'],
                            norm_params['close']['std']
                        )
                        features['close_1h_normalized'] = close_norm
                    
                    # Call normalization encoder for volume
                    if 'volume' in norm_params:
                        volume_norm = self.norm_calc.calculate(
                            hourly_data['volume'].tail(self.time_windows['1H']),
                            norm_params['volume']['mean'],
                            norm_params['volume']['std']
                        )
                        features['volume_1h_normalized'] = volume_norm
            
            # 2. Process 15-minute data (corresponds to branch E in flowchart)
            if len(df) >= self.time_windows['15m']:
                min15_data = df[df['bar'] == '15m'] if 'bar' in df.columns else df
                if len(min15_data) >= self.time_windows['15m']:
                    # Call RSI calculator
                    rsi_14_15m = self.rsi_calc.get_last_value(min15_data['close'].tail(self.time_windows['15m']))
                    features['rsi_14_15m'] = rsi_14_15m
                    
                    # Call volume impulse calculator
                    volume_impulse = self.impulse_calc.get_last_value(min15_data['volume'].tail(20))
                    features['volume_impulse_15m'] = volume_impulse
            
            # 3. Process 4-hour data (corresponds to branch F in flowchart)
            if len(df) >= self.time_windows['4H']:
                hour4_data = df[df['bar'] == '4H'] if 'bar' in df.columns else df
                if len(hour4_data) >= self.time_windows['4H']:
                    # Call RSI calculator
                    rsi_14_4h = self.rsi_calc.get_last_value(hour4_data['close'].tail(self.time_windows['4H']))
                    features['rsi_14_4h'] = rsi_14_4h
                    
                    # Call trend continuation calculator
                    trend_continuation = self.trend_calc.get_last_value(hour4_data['close'].tail(20))
                    features['trend_continuation_4h'] = trend_continuation
            
            # Add time encoding features
            if not df.empty:
                last_timestamp = df['timestamp'].iloc[-1] if 'timestamp' in df.columns else datetime.now().timestamp() * 1000
                hour_cos, hour_sin = self.time_calc.calculate(last_timestamp)
                features['hour_cos'] = hour_cos
                features['hour_sin'] = hour_sin
                features['day_of_week'] = pd.to_datetime(last_timestamp, unit='ms').dayofweek
            
            # Add timestamp for reference (will be removed before training)
            features['timestamp'] = last_timestamp
            
            return features
            
        except Exception as e:
            logger.error(f"Failed to extract features: {e}")
            return None
    
    def _generate_target(self, current_row: pd.Series, future_data: pd.DataFrame) -> int:
        """
        Generate classification target based on future price movement.
        Uses 7-level classification as specified in the architecture.
        """
        if future_data.empty:
            return 4  # Neutral class as default
        
        try:
            current_price = current_row['close']
            future_price = future_data['close'].iloc[-1]
            
            # Calculate percentage change
            pct_change = ((future_price - current_price) / current_price) * 100
            
            # 7-level classification thresholds
            thresholds = config.CLASSIFICATION_THRESHOLDS
            
            # Map percentage change to class
            for class_label, (min_val, max_val) in thresholds.items():
                if min_val <= pct_change < max_val:
                    return class_label
            
            # Default to neutral if outside all ranges
            return 4
            
        except Exception as e:
            logger.error(f"Failed to generate target: {e}")
            return 4  # Neutral class

# Global instance
feature_engineer = FeatureEngineer()