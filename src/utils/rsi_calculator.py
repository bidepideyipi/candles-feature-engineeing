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
    
    def __init__(self, window: int = 14):
        """
        Initialize RSI calculator
        
        Args:
            window: Number of periods for RSI calculation (default: 14)
        """
        self.window = window
    
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
        
        # Calculate average gain and loss
        avg_gain = gain.rolling(window=self.window, min_periods=1).mean()
        avg_loss = loss.rolling(window=self.window, min_periods=1).mean()
        
        # 避免除零导致的 inf/NaN
        avg_loss = avg_loss.replace(0, 1)  # 如果平均亏损为0，用1替代
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Handle division by zero
        rsi = rsi.replace([np.inf, -np.inf], np.nan)
        
        return self._get_last_value(rsi)
   
#Instance    
RSI_CALCULATOR = RSICalculator()