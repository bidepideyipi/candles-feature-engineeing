"""
Pinbar (K线形态) Calculator
Independent Pinbar calculation utility with standardized interface
"""

import pandas as pd
import numpy as np
from typing import Union, Tuple
from .calculator_interface import BaseTechnicalCalculator


class PinbarCalculator(BaseTechnicalCalculator):
    """Independent Pinbar calculator with customizable parameters and standardized interface"""
    
    def __init__(self, 
                 long_shadow_threshold: float = 1.0,
                 doji_threshold: float = 0.1):
        """
        Initialize Pinbar calculator
        
        Args:
            long_shadow_threshold: Threshold for long shadow (shadow > body * threshold, default: 1.0)
            doji_threshold: Threshold for doji (body < range * threshold, default: 0.1)
        """
        self.long_shadow_threshold = long_shadow_threshold
        self.doji_threshold = doji_threshold
    
    def calculate(self, 
                 high_prices: Union[pd.Series, list, np.ndarray],
                 low_prices: Union[pd.Series, list, np.ndarray],
                 open_prices: Union[pd.Series, list, np.ndarray],
                 close_prices: Union[pd.Series, list, np.ndarray]) -> dict:
        """
        Calculate Pinbar features
        
        Args:
            high_prices: High prices series
            low_prices: Low prices series
            open_prices: Open prices series
            close_prices: Close prices series
            
        Returns:
            Dictionary with pinbar features (latest values)
            {
                'upper_shadow': 10.5,              # 上引线长度
                'lower_shadow': 5.2,               # 下引线长度
                'body_height': 8.3,                # 实体高度
                'upper_shadow_ratio': 1.26,         # 上引线比例
                'lower_shadow_ratio': 0.63,         # 下引线比例
                'total_shadow_ratio': 0.55,         # 总影线比例
                'shadow_imbalance': 0.31,          # 影线不平衡度（正值=多头占优）
                'body_ratio': 0.45,                # 实体占比
                'is_long_upper_shadow': 1,          # 是否长上影线
                'is_long_lower_shadow': 0,          # 是否长下影线
                'is_doji': 0,                      # 是否十字星
                'shadow_type': 1                   # 影线类型（0=平衡, 1=长上影, 2=长下影, 3=长上下影）
            }
            
            0 无影线或平衡 趋势明确 
            1 长上影线 空头力量强，可能下跌 
            2 长下影线 多头力量强，可能上涨 
            3 长上下影线 多空分歧大，市场犹豫
        """
        high_series = self._convert_to_series(high_prices)
        low_series = self._convert_to_series(low_prices)
        open_series = self._convert_to_series(open_prices)
        close_series = self._convert_to_series(close_prices)
        
        if high_series.empty or low_series.empty or open_series.empty or close_series.empty:
            return self._get_empty_result()
        
        high = self._get_last_value(high_series)
        low = self._get_last_value(low_series)
        open_price = self._get_last_value(open_series)
        close_price = self._get_last_value(close_series)
        
        range_price = high - low
        
        if range_price <= 0:
            return self._get_empty_result()
        
        upper_shadow = high - max(open_price, close_price)
        lower_shadow = min(open_price, close_price) - low
        body_height = abs(close_price - open_price)
        
        upper_shadow_ratio = upper_shadow / body_height if body_height > 0 else 0
        lower_shadow_ratio = lower_shadow / body_height if body_height > 0 else 0
        total_shadow_ratio = (upper_shadow + lower_shadow) / range_price
        shadow_imbalance = (upper_shadow - lower_shadow) / range_price
        body_ratio = body_height / range_price
        
        is_long_upper_shadow = upper_shadow > body_height * self.long_shadow_threshold
        is_long_lower_shadow = lower_shadow > body_height * self.long_shadow_threshold
        is_doji = body_height < range_price * self.doji_threshold
        
        shadow_type = self._get_shadow_type(
            is_long_upper_shadow, 
            is_long_lower_shadow,
            upper_shadow,
            lower_shadow
        )
        
        return {
            'upper_shadow': upper_shadow,
            'lower_shadow': lower_shadow,
            'body_height': body_height,
            'upper_shadow_ratio': upper_shadow_ratio,
            'lower_shadow_ratio': lower_shadow_ratio,
            'total_shadow_ratio': total_shadow_ratio,
            'shadow_imbalance': shadow_imbalance,
            'body_ratio': body_ratio,
            'is_long_upper_shadow': int(is_long_upper_shadow),
            'is_long_lower_shadow': int(is_long_lower_shadow),
            'is_doji': int(is_doji),
            'shadow_type': shadow_type
        }
    
    def _get_shadow_type(self, is_long_upper: bool, is_long_lower: bool, upper: float, lower: float) -> int:
        """Determine shadow type"""
        if is_long_upper and not is_long_lower:
            return 1
        elif is_long_lower and not is_long_upper:
            return 2
        elif is_long_upper and is_long_lower:
            return 3
        else:
            return 0
    
    def _get_empty_result(self) -> dict:
        """Return empty result for invalid data"""
        return {
            'upper_shadow': 0,
            'lower_shadow': 0,
            'body_height': 0,
            'upper_shadow_ratio': 0,
            'lower_shadow_ratio': 0,
            'total_shadow_ratio': 0,
            'shadow_imbalance': 0,
            'body_ratio': 0,
            'is_long_upper_shadow': 0,
            'is_long_lower_shadow': 0,
            'is_doji': 0,
            'shadow_type': 0
        }


PINBAR_CALCULATOR = PinbarCalculator()
