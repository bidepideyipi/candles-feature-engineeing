"""
Technical indicators calculator for multiple time windows.
Calculates RSI, MACD, and BOLL indicators.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands

from ..config.settings import config

logger = logging.getLogger(__name__)

class TechnicalIndicatorsCalculator:
    """Calculates technical indicators for multiple time windows."""
    
    def __init__(self):
        """Initialize the calculator."""
        self.time_windows = config.TIME_WINDOWS
    
    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate all technical indicators for multiple time windows.
        
        Args:
            df: DataFrame with OHLCV data (columns: timestamp, open, high, low, close, volume)
            
        Returns:
            Dictionary containing indicators for all time windows
        """
        if len(df) < max(self.time_windows.values()):
            logger.warning(f"Insufficient data for indicator calculation. Need at least {max(self.time_windows.values())} periods.")
            return {}
        
        # Ensure data is sorted by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        indicators = {}
        
        # Calculate indicators for each time window
        for window_name, window_size in self.time_windows.items():
            if len(df) >= window_size:
                window_data = df.tail(window_size).copy()
                window_indicators = self._calculate_window_indicators(window_data, window_name)
                indicators.update(window_indicators)
            else:
                logger.warning(f"Not enough data for {window_name} window ({window_size} periods)")
        
        return indicators
    
    def _calculate_window_indicators(self, df: pd.DataFrame, window_name: str) -> Dict[str, float]:
        """
        Calculate indicators for a specific time window.
        
        Args:
            df: DataFrame with OHLCV data for the window
            window_name: Name of the time window (short, medium, long)
            
        Returns:
            Dictionary of indicator values
        """
        close_prices = df['close']
        high_prices = df['high']
        low_prices = df['low']
        volume = df['volume']
        
        indicators = {}
        
        try:
            # RSI (Relative Strength Index)
            rsi_indicator = RSIIndicator(close=close_prices, window=14)
            rsi_values = rsi_indicator.rsi()
            indicators[f'{window_name}_rsi'] = float(rsi_values.iloc[-1]) if not rsi_values.empty else np.nan
            
            # MACD (Moving Average Convergence Divergence)
            macd_indicator = MACD(close=close_prices, window_slow=26, window_fast=12, window_sign=9)
            macd_line = macd_indicator.macd()
            macd_signal = macd_indicator.macd_signal()
            macd_histogram = macd_indicator.macd_diff()
            
            indicators[f'{window_name}_macd'] = float(macd_line.iloc[-1]) if not macd_line.empty else np.nan
            indicators[f'{window_name}_macd_signal'] = float(macd_signal.iloc[-1]) if not macd_signal.empty else np.nan
            indicators[f'{window_name}_macd_histogram'] = float(macd_histogram.iloc[-1]) if not macd_histogram.empty else np.nan
            
            # BOLL (Bollinger Bands)
            boll_indicator = BollingerBands(close=close_prices, window=20, window_dev=2)
            bb_upper = boll_indicator.bollinger_hband()
            bb_lower = boll_indicator.bollinger_lband()
            bb_middle = boll_indicator.bollinger_mavg()
            
            current_price = close_prices.iloc[-1]
            upper_band = bb_upper.iloc[-1] if not bb_upper.empty else np.nan
            lower_band = bb_lower.iloc[-1] if not bb_lower.empty else np.nan
            middle_band = bb_middle.iloc[-1] if not bb_middle.empty else np.nan
            
            indicators[f'{window_name}_bb_upper'] = float(upper_band)
            indicators[f'{window_name}_bb_lower'] = float(lower_band)
            indicators[f'{window_name}_bb_middle'] = float(middle_band)
            
            # Bollinger Band position (0-1 scale)
            if not (np.isnan(upper_band) or np.isnan(lower_band)) and upper_band != lower_band:
                bb_position = (current_price - lower_band) / (upper_band - lower_band)
                indicators[f'{window_name}_bb_position'] = float(bb_position)
            else:
                indicators[f'{window_name}_bb_position'] = np.nan
            
            # Price position relative to moving average
            if not np.isnan(middle_band) and middle_band != 0:
                price_ma_ratio = current_price / middle_band
                indicators[f'{window_name}_price_ma_ratio'] = float(price_ma_ratio)
            else:
                indicators[f'{window_name}_price_ma_ratio'] = np.nan
            
        except Exception as e:
            logger.error(f"Error calculating {window_name} window indicators: {e}")
            # Return NaN for all indicators in case of error
            for indicator_type in ['rsi', 'macd', 'macd_signal', 'macd_histogram', 
                                 'bb_upper', 'bb_lower', 'bb_middle', 'bb_position', 'price_ma_ratio']:
                indicators[f'{window_name}_{indicator_type}'] = np.nan
        
        return indicators
    
    def calculate_price_features(self, df: pd.DataFrame, prediction_horizon: int = 24) -> Dict[str, Any]:
        """
        Calculate price-based features including future returns.
        
        Args:
            df: DataFrame with OHLCV data
            prediction_horizon: Number of periods to look ahead for return calculation
            
        Returns:
            Dictionary of price features
        """
        if len(df) < prediction_horizon + 1:
            logger.warning(f"Insufficient data for {prediction_horizon}-period return calculation")
            return {}
        
        df = df.sort_values('timestamp').reset_index(drop=True)
        current_close = df['close'].iloc[-1]
        
        features = {
            'current_price': float(current_close),
            'price_volatility': float(df['close'].tail(24).std() / df['close'].tail(24).mean()),  # 24-hour volatility
            'volume_avg': float(df['volume'].tail(24).mean()),
            'price_trend_24h': float((df['close'].iloc[-1] / df['close'].iloc[-25] - 1) * 100) if len(df) >= 25 else np.nan
        }
        
        # Future return (this will be our target variable for training)
        if len(df) >= prediction_horizon + 1:
            future_price = df['close'].iloc[-(prediction_horizon + 1)]
            future_return = (future_price / current_close - 1) * 100
            features['future_return'] = float(future_return)
            
            # Classification label based on return
            features['classification_label'] = self._classify_return(future_return)
        else:
            features['future_return'] = np.nan
            features['classification_label'] = None
        
        return features
    
    def _classify_return(self, return_pct: float) -> int:
        """
        Classify return percentage into discrete categories.
        
        Args:
            return_pct: Return percentage
            
        Returns:
            Classification label (-4 to 3)
        """
        for label, (min_val, max_val) in config.CLASSIFICATION_THRESHOLDS.items():
            if min_val <= return_pct < max_val:
                return label
        return 0  # Default to neutral class

# Global instance
tech_calculator = TechnicalIndicatorsCalculator()