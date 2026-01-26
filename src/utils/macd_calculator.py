"""
MACD (Moving Average Convergence Divergence) Calculator
Independent MACD calculation utility
"""

import pandas as pd
import numpy as np
from typing import Union, Tuple, Optional


class MACDCalculator:
    """Independent MACD calculator with customizable parameters"""
    
    def __init__(self, 
                 fast_window: int = 12, 
                 slow_window: int = 26, 
                 signal_window: int = 9):
        """
        Initialize MACD calculator
        
        Args:
            fast_window: Fast EMA period (default: 12)
            slow_window: Slow EMA period (default: 26)
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
        if not isinstance(close_prices, pd.Series):
            close_prices = pd.Series(close_prices)
        
        # Calculate EMAs
        ema_fast = close_prices.ewm(span=self.fast_window, adjust=False).mean()
        ema_slow = close_prices.ewm(span=self.slow_window, adjust=False).mean()
        
        # Calculate MACD line
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line
        signal_line = macd_line.ewm(span=self.signal_window, adjust=False).mean()
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def get_last_values(self, close_prices: Union[pd.Series, list, np.ndarray]) -> Tuple[float, float, float]:
        """
        Get the last MACD values
        
        Args:
            close_prices: Closing prices series
            
        Returns:
            Tuple of (last_macd, last_signal, last_histogram)
        """
        macd_line, signal_line, histogram = self.calculate(close_prices)
        
        last_macd = float(macd_line.iloc[-1]) if not macd_line.empty else np.nan
        last_signal = float(signal_line.iloc[-1]) if not signal_line.empty else np.nan
        last_histogram = float(histogram.iloc[-1]) if not histogram.empty else np.nan
        
        return last_macd, last_signal, last_histogram


# Convenience functions
def calculate_macd(close_prices: Union[pd.Series, list, np.ndarray],
                   fast_window: int = 12,
                   slow_window: int = 26,
                   signal_window: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Convenience function to calculate MACD
    
    Args:
        close_prices: Closing prices series
        fast_window: Fast EMA period (default: 12)
        slow_window: Slow EMA period (default: 26)
        signal_window: Signal line EMA period (default: 9)
        
    Returns:
        Tuple of (macd_line, signal_line, histogram)
    """
    calculator = MACDCalculator(
        fast_window=fast_window,
        slow_window=slow_window,
        signal_window=signal_window
    )
    return calculator.calculate(close_prices)


def get_macd_last(close_prices: Union[pd.Series, list, np.ndarray],
                  fast_window: int = 12,
                  slow_window: int = 26,
                  signal_window: int = 9) -> Tuple[float, float, float]:
    """
    Convenience function to get last MACD values
    
    Args:
        close_prices: Closing prices series
        fast_window: Fast EMA period (default: 12)
        slow_window: Slow EMA period (default: 26)
        signal_window: Signal line EMA period (default: 9)
        
    Returns:
        Tuple of (last_macd, last_signal, last_histogram)
    """
    calculator = MACDCalculator(
        fast_window=fast_window,
        slow_window=slow_window,
        signal_window=signal_window
    )
    return calculator.get_last_values(close_prices)