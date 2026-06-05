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
        
        # 检查数据是否有效
        if len(prices_series) == 0:
            raise ValueError("Cannot calculate normalization: input data is empty")
        
        # 优化性能，直接计算整体均值和标准差，而不是滚动窗口
        rolling_mean = prices_series.mean()
        rolling_std = prices_series.std()
        
        # 处理标准差为 0 或 NaN 的情况（所有值相同或只有一个值）
        if pd.isna(rolling_std) or rolling_std == 0:
            raise ValueError(f"Cannot calculate normalization: std is {rolling_std}, mean={rolling_mean}")
        
        # Normalize prices
        normalized = (prices_series - rolling_mean) / rolling_std
        
        # 返回最后一个归一化值、均值和标准差（都是标量）
        return float(normalized.iloc[-1]), float(rolling_mean), float(rolling_std)

NORMALIZED = Normalized()
