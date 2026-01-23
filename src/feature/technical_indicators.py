"""
Technical indicators calculator using assembly pattern.
Flexibly assemble different technical indicators.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union

from ..config.settings import config
from .indicator_interface import indicator_registry, TechnicalIndicator
from .indicators import RSIIndicator, MACDIndicator, BollingerBandsIndicator, PricePositionIndicator

logger = logging.getLogger(__name__)


class TechnicalIndicatorsCalculator:
    """Calculates technical indicators using assembly pattern for flexibility."""
    
    def __init__(self, indicators: Optional[List[Union[str, TechnicalIndicator]]] = None):
        """
        Initialize the calculator with specified indicators.
        
        Args:
            indicators: List of indicator names or instances. 
                       If None, uses default indicators.
        """
        self.time_windows = config.TIME_WINDOWS
        self.indicators = []
        
        if indicators is None:
            # Default indicators
            self.add_indicator(RSIIndicator(window=14))
            self.add_indicator(MACDIndicator(fast_window=12, slow_window=26, signal_window=9))
            self.add_indicator(BollingerBandsIndicator(window=20, num_std=2.0))
            self.add_indicator(PricePositionIndicator(window=20))
        else:
            # Add specified indicators
            for indicator in indicators:
                self.add_indicator(indicator)
    
    def add_indicator(self, indicator: Union[str, TechnicalIndicator], **kwargs):
        """
        Add an indicator to the calculator.
        
        Args:
            indicator: Either indicator name (str) or indicator instance
            **kwargs: Additional parameters for indicator creation
        """
        if isinstance(indicator, str):
            # Create indicator from registry
            indicator_instance = indicator_registry.create_instance(indicator, **kwargs)
        else:
            # Use provided indicator instance
            indicator_instance = indicator
        
        self.indicators.append(indicator_instance)
        logger.info(f"Added indicator: {indicator_instance.name}")
    
    def remove_indicator(self, indicator_name: str):
        """
        Remove an indicator from the calculator.
        
        Args:
            indicator_name: Name of the indicator to remove
        """
        self.indicators = [ind for ind in self.indicators if ind.name != indicator_name]
        logger.info(f"Removed indicator: {indicator_name}")
    
    def list_indicators(self) -> List[str]:
        """List all currently configured indicators."""
        return [indicator.name for indicator in self.indicators]
    
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
        Calculate indicators for a specific time window using assembly pattern.
        
        Args:
            df: DataFrame with OHLCV data for the window
            window_name: Name of the time window (short, medium, long)
            
        Returns:
            Dictionary of indicator values
        """
        indicators = {}
        
        try:
            # Calculate each configured indicator
            for indicator in self.indicators:
                # Check if we have required data
                if len(df) < indicator.min_periods:
                    # Return NaN values for this indicator
                    for key in indicator.calculate(df).values.keys():
                        indicators[f'{window_name}_{key}'] = np.nan
                    continue
                
                # Check required columns
                missing_columns = set(indicator.required_columns) - set(df.columns)
                if missing_columns:
                    logger.warning(f"Missing columns for {indicator.name}: {missing_columns}")
                    for key in indicator.calculate(df).values.keys():
                        indicators[f'{window_name}_{key}'] = np.nan
                    continue
                
                # Calculate indicator
                result = indicator.calculate(df)
                
                # Add results with window prefix
                for key, value in result.values.items():
                    indicators[f'{window_name}_{key}'] = float(value) if not np.isnan(value) else np.nan
                    
        except Exception as e:
            logger.error(f"Error calculating {window_name} window indicators: {e}")
            # Return NaN for all configured indicators
            for indicator in self.indicators:
                for key in indicator.calculate(df).values.keys():
                    indicators[f'{window_name}_{key}'] = np.nan
        
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


# Global instance with default indicators
tech_calculator = TechnicalIndicatorsCalculator()


# Convenience functions for common use cases
def create_custom_calculator(indicator_names: List[str], **indicator_params) -> TechnicalIndicatorsCalculator:
    """
    Create a calculator with custom indicators.
    
    Args:
        indicator_names: List of indicator names to include
        **indicator_params: Parameters for each indicator
        
    Returns:
        Configured TechnicalIndicatorsCalculator instance
    """
    indicators = []
    for name in indicator_names:
        params = indicator_params.get(name, {})
        indicators.append(indicator_registry.create_instance(name, **params))
    
    return TechnicalIndicatorsCalculator(indicators)


def get_available_indicators() -> List[str]:
    """Get list of all available indicator names."""
    return indicator_registry.list_indicators()