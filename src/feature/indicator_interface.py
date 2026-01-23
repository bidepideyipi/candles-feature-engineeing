"""
Technical Indicator Interface and Base Classes
Defines the contract for all technical indicators
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class IndicatorResult:
    """Standard result format for all indicators"""
    name: str
    values: Dict[str, float]
    metadata: Optional[Dict[str, Any]] = None


class TechnicalIndicator(ABC):
    """Abstract base class for all technical indicators"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> IndicatorResult:
        """
        Calculate the indicator values
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            IndicatorResult containing calculated values
        """
        pass
    
    @property
    @abstractmethod
    def required_columns(self) -> List[str]:
        """Return list of required DataFrame columns"""
        pass
    
    @property
    @abstractmethod
    def min_periods(self) -> int:
        """Return minimum number of periods required for calculation"""
        pass


class IndicatorRegistry:
    """Registry to manage available indicators"""
    
    def __init__(self):
        self._indicators = {}
    
    def register(self, indicator_class: type, name: str = None):
        """Register an indicator class"""
        indicator_name = name or indicator_class.__name__
        self._indicators[indicator_name] = indicator_class
        return indicator_class
    
    def get(self, name: str) -> type:
        """Get registered indicator class by name"""
        return self._indicators.get(name)
    
    def list_indicators(self) -> List[str]:
        """List all registered indicator names"""
        return list(self._indicators.keys())
    
    def create_instance(self, name: str, **kwargs) -> TechnicalIndicator:
        """Create an instance of a registered indicator"""
        indicator_class = self.get(name)
        if not indicator_class:
            raise ValueError(f"Indicator '{name}' not registered")
        return indicator_class(**kwargs)


# Global registry instance
indicator_registry = IndicatorRegistry()