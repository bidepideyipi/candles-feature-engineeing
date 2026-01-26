"""
RSI (Relative Strength Index) Calculator
Independent RSI calculation utility with standardized interface
"""

import pandas as pd
import numpy as np
from typing import Union
from .calculator_interface import BaseTechnicalCalculator

class RSICalculator(BaseTechnicalCalculator):
    """Independent RSI calculator with customizable parameters and standardized interface"""
    
    # def __init__(self, window: int = 14):
    #     """
    #     Initialize RSI calculator
        
    #     Args:
    #         window: Number of periods for RSI calculation (default: 14)
    #     """
    #     self.window = window
    
    def calculate(self, close_prices: Union[pd.Series, list, np.ndarray]) -> pd.Series:
        """
        Calculate RSI values
        
        Args:
            close_prices: Closing prices series
            
        Returns:
            pandas Series with RSI values
        """
        # Convert to pandas Series if needed
        prices_series = self._convert_to_series(close_prices)
        
        # Calculate price changes
        delta = prices_series.diff()
        
        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        window = len(prices_series)
        # Calculate average gain and loss
        avg_gain = gain.rolling(window=window, min_periods=1).mean()
        avg_loss = loss.rolling(window=window, min_periods=1).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Handle division by zero
        rsi = rsi.replace([np.inf, -np.inf], np.nan)
        
        return self._get_last_value(rsi)
    
RSI_CALCULATOR = RSICalculator()

# _rsi_calculators = {}


# def calculate_rsi(close_prices: Union[pd.Series, list, np.ndarray], 
#                   window: int = 14) -> pd.Series:
#     """
#     Convenience function to calculate RSI using cached calculator instances
    
#     Args:
#         close_prices: Closing prices series
#         window: Number of periods (default: 14)
        
#     Returns:
#         pandas Series with RSI values
#     """
#     # Use cached instance for common windows to avoid repeated instantiation
#     if window not in _rsi_calculators:
#         _rsi_calculators[window] = RSICalculator(window=window)
    
#     return _rsi_calculators[window].calculate(close_prices)


# def get_rsi_last(close_prices: Union[pd.Series, list, np.ndarray], 
#                  window: int = 14) -> float:
#     """
#     Convenience function to get last RSI value using cached calculator instances
    
#     Args:
#         close_prices: Closing prices series
#         window: Number of periods (default: 14)
        
#     Returns:
#         Last RSI value as float
#     """
#     # Use cached instance for common windows to avoid repeated instantiation
#     if window not in _rsi_calculators:
#         _rsi_calculators[window] = RSICalculator(window=window)
    
#     return _rsi_calculators[window].get_last(close_prices)