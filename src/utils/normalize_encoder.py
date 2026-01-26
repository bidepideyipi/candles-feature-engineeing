"""
Normalized Price Calculator
Implements rolling window normalization with consistent interface
"""

import pandas as pd
import numpy as np
from typing import Union
from .calculator_interface import BaseTechnicalCalculator


class Normalized(BaseTechnicalCalculator):
    """Rolling window normalization calculator with standardized interface"""
    
    def calculate(self, close_prices: Union[pd.Series, list, np.ndarray]) -> pd.Series:
        """
        Calculate normalized price values using rolling window
        
        Note: For window=N, only indices N-1 and beyond contain accurate normalized values
        Indices 0 to N-2 will have incomplete window calculations
        
        Args:
            close_prices: Closing prices series
            
        Returns:
            pandas Series with normalized values
        """
        # Convert to pandas Series if needed
        prices_series = self._convert_to_series(close_prices)
        
        # Calculate rolling statistics
        window = len(prices_series)
        rolling_mean = prices_series.rolling(window=window, min_periods=1).mean()
        rolling_std = prices_series.rolling(window=window, min_periods=1).std()
        
        # Normalize prices
        normalized = (prices_series - rolling_mean) / rolling_std
        
        return self._get_last_value(normalized)

NORMALIZED = Normalized()
