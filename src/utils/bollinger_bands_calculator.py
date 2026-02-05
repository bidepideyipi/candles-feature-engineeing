"""
BOLL (Bollinger Bands) Calculator
Independent Bollinger Bands calculation utility
"""

import pandas as pd
import numpy as np
from typing import Union, Tuple, Optional
from .calculator_interface import BaseTechnicalCalculator


class BollingerBandsCalculator(BaseTechnicalCalculator):
    """Independent Bollinger Bands calculator with customizable parameters"""
    
    def __init__(self, 
                 window: int = 20, 
                 num_std: float = 2.0, 
                 fillna: bool = False):
        """
        Initialize Bollinger Bands calculator
        
        Args:
            window: Number of periods for moving average (default: 20)
            num_std: Number of standard deviations (default: 2.0)
            fillna: Whether to fill NaN values (default: False)
        """
        self.window = window
        self.num_std = num_std
        self.fillna = fillna
    
    def calculate(self, close_prices: Union[pd.Series, list, np.ndarray]) -> Tuple[float, float, float]:
        """
        Calculate Bollinger Bands latest values
        
        Args:
            close_prices: Closing prices series
            
        Returns:
            Tuple of (bollinger_upper, bollinger_lower, bollinger_position)
            - bollinger_upper: Latest upper band value (布林带上轨)
            - bollinger_lower: Latest lower band value (布林带下轨)
            - bollinger_position: Latest position (0-1 range, 布林带位置)
        """
        prices_series = self._convert_to_series(close_prices)
        
        # Calculate middle band (moving average)
        middle_band = prices_series.rolling(window=self.window, min_periods=1).mean()
        
        # Calculate standard deviation
        std_dev = prices_series.rolling(window=self.window, min_periods=1).std()
        
        # Calculate upper and lower bands
        upper_band = middle_band + (std_dev * self.num_std)
        lower_band = middle_band - (std_dev * self.num_std)
        
        # Calculate position (0-1 scale)
        band_width = upper_band - lower_band
        position = (prices_series - lower_band) / band_width
        
        # Handle division by zero and invalid values
        position = position.replace([np.inf, -np.inf], np.nan)
        position = position.clip(0, 1)
        
        # Fill NaN values if requested
        if self.fillna:
            upper_band = upper_band.fillna(prices_series)
            middle_band = middle_band.fillna(prices_series)
            lower_band = lower_band.fillna(prices_series)
            position = position.fillna(0.5)
        
        # Get latest values
        last_upper = self._get_last_value(upper_band)
        last_lower = self._get_last_value(lower_band)
        last_position = self._get_last_value(position)
        
        return last_upper, last_lower, last_position


# Pre-configured calculator instance
BOLLINGER_BANDS_20 = BollingerBandsCalculator(window=20, num_std=2.5)