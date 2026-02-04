"""
EMA (Exponential Moving Average) Calculator
Independent EMA calculation utility with standardized interface
"""

import pandas as pd
import numpy as np
from typing import Union
from .calculator_interface import BaseTechnicalCalculator

class EMACalculator(BaseTechnicalCalculator):
    """Independent EMA calculator with customizable parameters and standardized interface"""
    
    def __init__(self, window: int = 12):
        """
        Initialize EMA calculator
        
        Args:
            window: Number of periods for EMA calculation (default: 12)
        """
        self.window = window
    
    def calculate(self, close_prices: Union[pd.Series, list, np.ndarray]) -> float:
        """
        Calculate EMA value
        
        Args:
            close_prices: Closing prices series
            
        Returns:
            Latest EMA value
        """
        prices_series = self._convert_to_series(close_prices)
        
        if len(prices_series) < self.window:
            raise ValueError(f"Need at least {self.window} data points to calculate EMA")
        
        ema = prices_series.ewm(span=self.window, adjust=False).mean()
        
        return self._get_last_value(ema)

# Convenience instances for common periods
EMA_12 = EMACalculator(window=12)
EMA_26 = EMACalculator(window=26)
EMA_50 = EMACalculator(window=50)
