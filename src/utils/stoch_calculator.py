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
        Calculate Stochastic Oscillator values 随机振荡器
        是一个 动量指标 ，用于比较某个证券的 收盘价 与其 特定时间窗口内的价格范围 （最高价和最低价）之间的关系。
        收盘价往往接近价格区间的高端时，表明 上涨动能 （超买）
        收盘价往往接近价格区间的低端时，表明 下跌动能 （超卖）
        
        0-20 超卖区域 - 可能反弹 
        20-80 正常区域 - 没有明确信号 
        80-100 超买区域 - 可能回调
        
        Stochastic 在横盘时容易产生假信号

        解决：
        - 结合其他指标（如 RSI、MACD）
        - 等待价格突破确认
        - 在强势趋势中谨慎使用超买/超卖信号
        
        与其他指标对比
        RSI 都是 0-100 的振荡器 RSI 只看收盘价，Stochastic 考虑高低价范围 
        MACD 都有交叉信号 Stochastic 反应更快，但噪音更多 
        ATR 都涉及价格波动 ATR 测量波动幅度，Stochastic 测量相对位置
        
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
