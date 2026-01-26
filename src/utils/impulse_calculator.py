#计算成交量脉冲

import pandas as pd
import numpy as np
from typing import Union
from .calculator_interface import BaseTechnicalCalculator

class ImpulseCalculator(BaseTechnicalCalculator):
   
    def calculate(self, volume_series: Union[pd.Series, list, np.ndarray]) -> pd.Series:
        """
        计算成交量脉冲指标
        
        Args:
            volume_series: 成交量时间序列
        
        Returns:
            volume_impulse: 成交量相对于近期平均水平的倍数
        """
        window = len(volume_series)
        # 计算近期平均成交量
        avg_volume = volume_series.rolling(window=window, min_periods=1).mean()
        
        # 计算成交量脉冲（当前成交量相对平均值的比例）
        volume_impulse = volume_series / avg_volume
        
        return self._get_last_value(volume_impulse)
    
IMPULSE_CALCULATOR = ImpulseCalculator()
