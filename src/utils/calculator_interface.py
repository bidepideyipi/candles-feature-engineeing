"""
Technical Indicator Calculator Interface
Defines the common interface for all technical indicator calculators
"""

import pandas as pd
import numpy as np
from typing import Union, Protocol, TypeVar, Tuple
from abc import ABC, abstractmethod

# Type variables for generic return types
T = TypeVar('T')
SeriesType = Union[pd.Series, list, np.ndarray]

class TechnicalCalculator(Protocol):
    """
    Protocol defining the common interface for technical indicator calculators
    """
    
    def calculate(self, close_prices: SeriesType) -> Union[pd.Series, Tuple[pd.Series, ...]]:
        """
        Calculate the technical indicator values
        
        Args:
            close_prices: Closing prices series
            
        Returns:
            Calculated indicator values (single Series or tuple of Series)
        """
        ...


class BaseTechnicalCalculator(ABC):
    """
    Abstract base class for technical indicator calculators
    Provides common functionality and interface enforcement
    """
    
    @abstractmethod
    def calculate(self, close_prices: SeriesType) -> Union[pd.Series, Tuple[pd.Series, ...]]:
        """
        Calculate the technical indicator values
        
        Args:
            close_prices: Closing prices series
            
        Returns:
            Calculated indicator values
        """
        pass
    
    # def get_last(self, close_prices: SeriesType, windows: int) -> Union[float, Tuple[float, ...]]:
    #     """
    #     Get the last calculated value(s)
        
    #     Args:
    #         close_prices: Closing prices series
            
    #     Returns:
    #         Last value(s)
    #     """
    #     calculated = self.calculate(close_prices, windows)
    #     return self._get_last_value(calculated)
    
    def _convert_to_series(self, data: SeriesType) -> pd.Series:
        """
        Convert input data to pandas Series if needed
        
        Args:
            data: Input data (Series, list, or numpy array)
            
        Returns:
            pandas Series
        """
        if not isinstance(data, pd.Series):
            return pd.Series(data)
        return data
    
    def _get_last_value(self, series: pd.Series) -> float:
        """
        Safely get the last value from a series
        
        Args:
            series: pandas Series
            
        Returns:
            Last value as float, or NaN if series is empty
        """
        if series.empty:
            return np.nan
        return float(series.iloc[-1])