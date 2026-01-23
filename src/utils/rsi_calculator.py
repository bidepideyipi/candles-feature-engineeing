"""
RSI (Relative Strength Index) Calculator
Independent RSI calculation utility
"""

import pandas as pd
import numpy as np
from typing import Union, Optional


class RSICalculator:
    """Independent RSI calculator with customizable parameters"""
    
    def __init__(self, window: int = 14, fillna: bool = False):
        """
        Initialize RSI calculator
        
        Args:
            window: Number of periods for RSI calculation (default: 14)
            fillna: Whether to fill NaN values (default: False)
        """
        self.window = window
        self.fillna = fillna
    
    def calculate(self, close_prices: Union[pd.Series, list, np.ndarray]) -> pd.Series:
        """
        Calculate RSI values
        
        Args:
            close_prices: Closing prices series
            
        Returns:
            pandas Series with RSI values
        """
        # Convert to pandas Series if needed
        if not isinstance(close_prices, pd.Series):
            close_prices = pd.Series(close_prices)
        
        # Calculate price changes
        delta = close_prices.diff()
        
        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calculate average gain and loss
        avg_gain = gain.rolling(window=self.window, min_periods=1).mean()
        avg_loss = loss.rolling(window=self.window, min_periods=1).mean()
        
        # For the first window periods, use simple average
        for i in range(self.window, len(avg_gain)):
            avg_gain.iloc[i] = ((avg_gain.iloc[i-1] * (self.window - 1)) + gain.iloc[i]) / self.window
            avg_loss.iloc[i] = ((avg_loss.iloc[i-1] * (self.window - 1)) + loss.iloc[i]) / self.window
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Handle division by zero
        rsi = rsi.replace([np.inf, -np.inf], np.nan)
        
        # Fill NaN values if requested
        if self.fillna:
            rsi = rsi.fillna(50)
        
        return rsi
    
    def get_last_value(self, close_prices: Union[pd.Series, list, np.ndarray]) -> float:
        """
        Get the last RSI value
        
        Args:
            close_prices: Closing prices series
            
        Returns:
            Last RSI value as float
        """
        rsi_series = self.calculate(close_prices)
        return float(rsi_series.iloc[-1]) if not rsi_series.empty else np.nan


# Convenience functions
def calculate_rsi(close_prices: Union[pd.Series, list, np.ndarray], 
                  window: int = 14, 
                  fillna: bool = False) -> pd.Series:
    """
    Convenience function to calculate RSI
    
    Args:
        close_prices: Closing prices series
        window: Number of periods (default: 14)
        fillna: Whether to fill NaN values (default: False)
        
    Returns:
        pandas Series with RSI values
    """
    calculator = RSICalculator(window=window, fillna=fillna)
    return calculator.calculate(close_prices)


def get_rsi_last(close_prices: Union[pd.Series, list, np.ndarray], 
                 window: int = 14) -> float:
    """
    Convenience function to get last RSI value
    
    Args:
        close_prices: Closing prices series
        window: Number of periods (default: 14)
        
    Returns:
        Last RSI value as float
    """
    calculator = RSICalculator(window=window)
    return calculator.get_last_value(close_prices)