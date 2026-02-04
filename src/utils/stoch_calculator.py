"""
Stochastic Oscillator Calculator
Independent Stochastic calculation utility with standardized interface
"""

import pandas as pd
import numpy as np
from typing import Union, Tuple
from .calculator_interface import BaseTechnicalCalculator

class StochasticCalculator(BaseTechnicalCalculator):
    """Independent Stochastic calculator with customizable parameters and standardized interface"""
    
    def __init__(self, k_window: int = 14, d_window: int = 3):
        """
        Initialize Stochastic calculator
        
        Args:
            k_window: Period for %K calculation (default: 14)
            d_window: Period for %D calculation (default: 3)
        """
        self.k_window = k_window
        self.d_window = d_window
    
    def calculate(self, df: pd.DataFrame) -> Tuple[float, float]:
        """
        Calculate Stochastic Oscillator values
        
        Args:
            df: DataFrame with OHLC data containing 'high', 'low', 'close' columns
            
        Returns:
            Tuple of (%K, %D)
        """
        required_cols = ['high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")
        
        high_prices = df['high'].astype(float)
        low_prices = df['low'].astype(float)
        close_prices = df['close'].astype(float)
        
        if len(high_prices) < self.k_window:
            raise ValueError(f"Need at least {self.k_window} data points to calculate Stochastic")
        
        lowest_low = low_prices.rolling(window=self.k_window).min()
        highest_high = high_prices.rolling(window=self.k_window).max()
        
        k_percent = 100 * ((close_prices - lowest_low) / (highest_high - lowest_low))
        
        d_percent = k_percent.rolling(window=self.d_window).mean()
        
        last_k = self._get_last_value(k_percent)
        last_d = self._get_last_value(d_percent)
        
        return last_k, last_d

# Convenience instance for default parameters
STOCH_CALCULATOR = StochasticCalculator()
