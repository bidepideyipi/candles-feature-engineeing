#计算成交量脉冲

import pandas as pd
import numpy as np
from typing import Union
from .calculator_interface import BaseTechnicalCalculator

class ImpulseCalculator(BaseTechnicalCalculator):
   
    def calculate(self, volume_series: Union[pd.Series, list, np.ndarray]) -> pd.Series:
        """
        计算成交量脉冲指标
        Volume Impulse Indicator (VIM) 成交量脉冲指标
        短期敏感性：15分钟级别需要较短的回顾窗口来捕捉即时的成交量激增
        统计稳定性：至少需要15-20个数据点才能得到稳定的平均值
        市场节奏匹配：
        加密货币市场24小时交易，短期波动频繁
        20-30周期能在保持敏感性的同时提供足够的基准参考
        Args:
            volume_series: 成交量时间序列
        
        Returns:
            volume_impulse: 成交量相对于近期平均水平的倍数
        """
        # 计算近期平均成交量
        # 使用shift(1)将平均值序列向前错位一天，解决了当前成交量与平均成交量计算时的对齐问题
        # 比如窗口为7 [1,1,1,1,1,1,1,2]  这个2应该是2.0，如果使用shift(1)前的计算方式会是1.78
        avg_volume = volume_series.rolling(window=20, min_periods=1).mean().shift(1)
        
        # 避免除零导致的 NaN
        avg_volume = avg_volume.replace(0, 1)  # 如果平均成交量为0，用1替代
        
        # 计算成交量脉冲（当前成交量相对平均值的比例）
        volume_impulse = volume_series / avg_volume
        
        return self._get_last_value(volume_impulse)
    
IMPULSE_CALCULATOR = ImpulseCalculator()
