"""
Support/Resistance Level Calculator
Calculates distance to nearest support/resistance levels
"""

import pandas as pd
import numpy as np
from typing import Union, Tuple
from .calculator_interface import BaseTechnicalCalculator

class SupportResistanceCalculator(BaseTechnicalCalculator):
    """Calculator for support and resistance level distances"""
    
    def __init__(self, window: int = 20, min_touches: int = 2):
        """
        Initialize support/resistance calculator
        
        Args:
            window: Lookback window for identifying support/resistance levels
            min_touches: Minimum number of touches to qualify as support/resistance
        """
        self.window = window
        self.min_touches = min_touches
    
    def calculate(self, df: pd.DataFrame) -> Tuple[float, float]:
        """
        Calculate support and resistance distances
        
        Args:
            df: DataFrame with OHLC data containing 'high', 'low', 'close' columns
            
        Returns:
            Tuple of (support_distance, resistance_distance)
        """
        # Validate required columns
        required_cols = ['high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")
        
        # Get current price
        current_price = float(df['close'].iloc[-1])
        
        # Find support and resistance levels
        support_level = self._find_support_level(df)
        resistance_level = self._find_resistance_level(df)
        
        # Calculate distances (normalized by current price)
        if support_level is not None:
            support_distance = (current_price - support_level) / current_price
        else:
            support_distance = np.nan
            
        if resistance_level is not None:
            resistance_distance = (resistance_level - current_price) / current_price
        else:
            resistance_distance = np.nan
        
        return support_distance, resistance_distance
    
    def _find_support_level(self, df: pd.DataFrame) -> float:
        """Find the nearest support level"""
        # Method 1: Pivot lows within lookback window
        lows = df['low'].tail(self.window)
        closes = df['close'].tail(self.window)
        
        # Find local minima (pivot lows)
        pivot_lows = []
        for i in range(1, len(lows) - 1):
            if (lows.iloc[i] < lows.iloc[i-1] and 
                lows.iloc[i] < lows.iloc[i+1] and
                lows.iloc[i] < closes.iloc[i]):  # Price closed above the low
                pivot_lows.append(lows.iloc[i])
        
        if not pivot_lows:
            return None
            
        # Return the highest pivot low (nearest support)
        return max(pivot_lows)
    
    def _find_resistance_level(self, df: pd.DataFrame) -> float:
        """Find the nearest resistance level"""
        # Method 1: Pivot highs within lookback window
        highs = df['high'].tail(self.window)
        closes = df['close'].tail(self.window)
        
        # Find local maxima (pivot highs)
        pivot_highs = []
        for i in range(1, len(highs) - 1):
            if (highs.iloc[i] > highs.iloc[i-1] and 
                highs.iloc[i] > highs.iloc[i+1] and
                highs.iloc[i] > closes.iloc[i]):  # Price closed below the high
                pivot_highs.append(highs.iloc[i])
        
        if not pivot_highs:
            return None
            
        # Return the lowest pivot high (nearest resistance)
        return min(pivot_highs)

# Global instance
SUPPORT_RESISTANCE_CALCULATOR = SupportResistanceCalculator()

# Convenience functions
def calculate_support_resistance_distance(df: pd.DataFrame, 
                                        window: int = 20) -> Tuple[float, float]:
    """
    Convenience function to calculate support/resistance distances
    
    Args:
        df: DataFrame with OHLC data
        window: Lookback window (default: 20)
        
    Returns:
        Tuple of (support_distance, resistance_distance)
    """
    calculator = SupportResistanceCalculator(window=window)
    return calculator.calculate(df)