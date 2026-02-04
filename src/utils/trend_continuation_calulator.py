#计算趋势延续强度

import pandas as pd
import numpy as np
from typing import Union
from .calculator_interface import BaseTechnicalCalculator

class TrendContinuationCalculator(BaseTechnicalCalculator):
    def calculate(self, close_prices: Union[pd.Series, list, np.ndarray]) -> pd.Series:
        """
        计算趋势延续强度
        关注点: 当前趋势会继续吗？
        正值 → 上涨趋势
        - 值越大，上涨越强势且连续
        负值 → 下跌趋势
        - 值越小（越负），下跌越强势且连续
        接近 0 → 震荡/无趋势
        
        Args:
            close_prices: 价格序列
        
        Returns:
            trend_continuation_score: 趋势延续分数 (-1到1)
        """
        # Convert to pandas Series if needed (using inherited method)
        prices_series = self._convert_to_series(close_prices)
        
        # 1. 计算价格变化方向
        price_changes = prices_series.diff()
        up_moves = (price_changes > 0).sum()
        down_moves = (price_changes < 0).sum()
        
        # 2. 计算趋势强度
        total_moves = up_moves + down_moves
        if total_moves == 0:
            return 0
        
        trend_strength = (up_moves - down_moves) / total_moves
        
        # 3. 计算价格延续性
        consecutive_same_direction = 0
        max_consecutive = 0
        
        for i in range(1, len(price_changes)):
            if (price_changes.iloc[i] > 0) == (price_changes.iloc[i-1] > 0):
                consecutive_same_direction += 1
                max_consecutive = max(max_consecutive, consecutive_same_direction)
            else:
                consecutive_same_direction = 0
        
        # 4. 综合评分
        continuation_score = trend_strength * (max_consecutive / len(price_changes))
        
        return continuation_score
    
TREND_CONTINUATION_CALCULATOR = TrendContinuationCalculator()
