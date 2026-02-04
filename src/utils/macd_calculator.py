"""
MACD (Moving Average Convergence Divergence) Calculator
Independent MACD calculation utility with standardized interface
"""

import pandas as pd
import numpy as np
from typing import Union, Tuple
from .calculator_interface import BaseTechnicalCalculator


class MACDCalculator(BaseTechnicalCalculator):
    """Independent MACD calculator with customizable parameters and standardized interface"""
    
    def __init__(self, 
                 fast_window: int = 12, 
                 slow_window: int = 48, 
                 signal_window: int = 9):
        """
        Initialize MACD calculator
        
        Args:
            fast_window: Fast EMA period (default: 12)
            slow_window: Slow EMA period (default: 48)
            signal_window: Signal line EMA period (default: 9)
        """
        self.fast_window = fast_window
        self.slow_window = slow_window
        self.signal_window = signal_window
    
    def calculate(self, close_prices: Union[pd.Series, list, np.ndarray]) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD values
        
        Args:
            close_prices: Closing prices series
            
        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        # Convert to pandas Series if needed
        prices_series = self._convert_to_series(close_prices)
        
        # Calculate EMAs
        ema_fast = prices_series.ewm(span=self.fast_window, adjust=False).mean()
        ema_slow = prices_series.ewm(span=self.slow_window, adjust=False).mean()
        
        # Calculate MACD line
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line
        signal_line = macd_line.ewm(span=self.signal_window, adjust=False).mean()
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        last_macd = self._get_last_value(macd_line)
        last_signal = self._get_last_value(signal_line)
        last_histogram = self._get_last_value(histogram)
        
        return last_macd, last_signal, last_histogram

# Convenience instance for default parameters
MACD_CALCULATOR = MACDCalculator()

