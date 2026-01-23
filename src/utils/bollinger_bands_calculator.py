"""
BOLL (Bollinger Bands) Calculator
Independent Bollinger Bands calculation utility
"""

import pandas as pd
import numpy as np
from typing import Union, Tuple, Optional


class BollingerBandsCalculator:
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
    
    def calculate(self, close_prices: Union[pd.Series, list, np.ndarray]) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands values
        
        Args:
            close_prices: Closing prices series
            
        Returns:
            Tuple of (upper_band, middle_band, lower_band)
        """
        # Convert to pandas Series if needed
        if not isinstance(close_prices, pd.Series):
            close_prices = pd.Series(close_prices)
        
        # Calculate middle band (moving average)
        middle_band = close_prices.rolling(window=self.window, min_periods=1).mean()
        
        # Calculate standard deviation
        std_dev = close_prices.rolling(window=self.window, min_periods=1).std()
        
        # Calculate upper and lower bands
        upper_band = middle_band + (std_dev * self.num_std)
        lower_band = middle_band - (std_dev * self.num_std)
        
        # Fill NaN values if requested
        if self.fillna:
            upper_band = upper_band.fillna(close_prices)
            middle_band = middle_band.fillna(close_prices)
            lower_band = lower_band.fillna(close_prices)
        
        return upper_band, middle_band, lower_band
    
    def calculate_with_position(self, close_prices: Union[pd.Series, list, np.ndarray]) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands with position indicator
        
        Args:
            close_prices: Closing prices series
            
        Returns:
            Tuple of (upper_band, middle_band, lower_band, position)
            Position is normalized between 0 and 1 (0 = lower band, 1 = upper band)
        """
        upper_band, middle_band, lower_band = self.calculate(close_prices)
        
        # Convert to pandas Series if needed
        if not isinstance(close_prices, pd.Series):
            close_prices = pd.Series(close_prices)
        
        # Calculate position (0-1 scale)
        band_width = upper_band - lower_band
        position = (close_prices - lower_band) / band_width
        
        # Handle division by zero and invalid values
        position = position.replace([np.inf, -np.inf], np.nan)
        position = position.clip(0, 1)  # Ensure values are between 0 and 1
        
        # Fill NaN values if requested
        if self.fillna:
            position = position.fillna(0.5)  # Default to middle position
        
        return upper_band, middle_band, lower_band, position
    
    def get_last_values(self, close_prices: Union[pd.Series, list, np.ndarray]) -> Tuple[float, float, float]:
        """
        Get the last Bollinger Bands values
        
        Args:
            close_prices: Closing prices series
            
        Returns:
            Tuple of (last_upper, last_middle, last_lower)
        """
        upper_band, middle_band, lower_band = self.calculate(close_prices)
        
        last_upper = float(upper_band.iloc[-1]) if not upper_band.empty else np.nan
        last_middle = float(middle_band.iloc[-1]) if not middle_band.empty else np.nan
        last_lower = float(lower_band.iloc[-1]) if not lower_band.empty else np.nan
        
        return last_upper, last_middle, last_lower
    
    def get_last_with_position(self, close_prices: Union[pd.Series, list, np.ndarray]) -> Tuple[float, float, float, float]:
        """
        Get the last Bollinger Bands values with position
        
        Args:
            close_prices: Closing prices series
            
        Returns:
            Tuple of (last_upper, last_middle, last_lower, last_position)
        """
        upper_band, middle_band, lower_band, position = self.calculate_with_position(close_prices)
        
        last_upper = float(upper_band.iloc[-1]) if not upper_band.empty else np.nan
        last_middle = float(middle_band.iloc[-1]) if not middle_band.empty else np.nan
        last_lower = float(lower_band.iloc[-1]) if not lower_band.empty else np.nan
        last_position = float(position.iloc[-1]) if not position.empty else np.nan
        
        return last_upper, last_middle, last_lower, last_position


# Convenience functions
def calculate_bollinger_bands(close_prices: Union[pd.Series, list, np.ndarray],
                              window: int = 20,
                              num_std: float = 2.0,
                              fillna: bool = False) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Convenience function to calculate Bollinger Bands
    
    Args:
        close_prices: Closing prices series
        window: Number of periods (default: 20)
        num_std: Number of standard deviations (default: 2.0)
        fillna: Whether to fill NaN values (default: False)
        
    Returns:
        Tuple of (upper_band, middle_band, lower_band)
    """
    calculator = BollingerBandsCalculator(window=window, num_std=num_std, fillna=fillna)
    return calculator.calculate(close_prices)


def calculate_bollinger_bands_with_position(close_prices: Union[pd.Series, list, np.ndarray],
                                           window: int = 20,
                                           num_std: float = 2.0,
                                           fillna: bool = False) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Convenience function to calculate Bollinger Bands with position
    
    Args:
        close_prices: Closing prices series
        window: Number of periods (default: 20)
        num_std: Number of standard deviations (default: 2.0)
        fillna: Whether to fill NaN values (default: False)
        
    Returns:
        Tuple of (upper_band, middle_band, lower_band, position)
    """
    calculator = BollingerBandsCalculator(window=window, num_std=num_std, fillna=fillna)
    return calculator.calculate_with_position(close_prices)


def get_bollinger_bands_last(close_prices: Union[pd.Series, list, np.ndarray],
                            window: int = 20,
                            num_std: float = 2.0) -> Tuple[float, float, float]:
    """
    Convenience function to get last Bollinger Bands values
    
    Args:
        close_prices: Closing prices series
        window: Number of periods (default: 20)
        num_std: Number of standard deviations (default: 2.0)
        
    Returns:
        Tuple of (last_upper, last_middle, last_lower)
    """
    calculator = BollingerBandsCalculator(window=window, num_std=num_std)
    return calculator.get_last_values(close_prices)


def get_bollinger_bands_last_with_position(close_prices: Union[pd.Series, list, np.ndarray],
                                          window: int = 20,
                                          num_std: float = 2.0) -> Tuple[float, float, float, float]:
    """
    Convenience function to get last Bollinger Bands values with position
    
    Args:
        close_prices: Closing prices series
        window: Number of periods (default: 20)
        num_std: Number of standard deviations (default: 2.0)
        
    Returns:
        Tuple of (last_upper, last_middle, last_lower, last_position)
    """
    calculator = BollingerBandsCalculator(window=window, num_std=num_std)
    return calculator.get_last_with_position(close_prices)