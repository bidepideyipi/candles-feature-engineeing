"""
ADX (Average Directional Index) Calculator
Independent ADX calculation utility with standardized interface
"""

import pandas as pd
import numpy as np
from typing import Tuple
from .calculator_interface import BaseTechnicalCalculator

class ADXCalculator(BaseTechnicalCalculator):
    """Independent ADX calculator with customizable parameters and standardized interface"""
    
    def __init__(self, window: int = 14):
        """
        Initialize ADX calculator
        
        Args:
            window: Number of periods for ADX calculation (default: 14)
        """
        self.window = window
    
    def calculate(self, df: pd.DataFrame) -> Tuple[float, float, float]:
        """
        Calculate ADX values
        Average Directional Index
        关注点: 当前趋势有多强？
        
        ADX值  趋势强度 交易策略 
        0-25    无趋势/弱趋势    区间交易，避免趋势策略 
        25-50   中等趋势        可使用趋势跟随 
        50-75   强趋势          趋势跟踪策略有效 
        75-100  极强趋势        注意风险，谨慎开仓
        
        Args:
            df: DataFrame with OHLC data containing 'high', 'low', 'close' columns
            
        Returns:
            Tuple of (adx, plus_di, minus_di)
        """
        required_cols = ['high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")
        
        high_prices = df['high'].astype(float)
        low_prices = df['low'].astype(float)
        close_prices = df['close'].astype(float)
        
        if len(high_prices) < self.window * 2:
            raise ValueError(f"Need at least {self.window * 2} data points to calculate ADX")
        
        # 1. Calculate True Range (TR) - same as ATR
        tr_list = []
        for i in range(len(high_prices)):
            if i == 0:
                tr = high_prices[i] - low_prices[i]
            else:
                method1 = high_prices[i] - low_prices[i]
                method2 = abs(high_prices[i] - close_prices[i-1])
                method3 = abs(low_prices[i] - close_prices[i-1])
                tr = max(method1, method2, method3)
            tr_list.append(tr)
        
        tr_series = pd.Series(tr_list)
        
        # 2. Calculate Directional Movements (+DM and -DM)
        plus_dm = []
        minus_dm = []
        
        for i in range(1, len(high_prices)):
            up_move = high_prices[i] - high_prices[i-1]
            down_move = low_prices[i-1] - low_prices[i]
            
            if up_move > down_move and up_move > 0:
                plus_dm.append(up_move)
            else:
                plus_dm.append(0)
            
            if down_move > up_move and down_move > 0:
                minus_dm.append(down_move)
            else:
                minus_dm.append(0)
        
        plus_dm_series = pd.Series([0] + plus_dm)
        minus_dm_series = pd.Series([0] + minus_dm)
        
        # 3. Smooth TR, +DM, -DM
        tr_smooth = tr_series.rolling(window=self.window, min_periods=1).mean()
        plus_dm_smooth = plus_dm_series.rolling(window=self.window, min_periods=1).mean()
        minus_dm_smooth = minus_dm_series.rolling(window=self.window, min_periods=1).mean()
        
        # 4. Calculate +DI and -DI
        plus_di = 100 * (plus_dm_smooth / tr_smooth)
        minus_di = 100 * (minus_dm_smooth / tr_smooth)
        
        # Handle division by zero
        plus_di = plus_di.replace([np.inf, -np.inf], np.nan)
        minus_di = minus_di.replace([np.inf, -np.inf], np.nan)
        
        # 5. Calculate DX (Directional Index)
        dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
        dx = dx.replace([np.inf, -np.inf], np.nan)
        
        # 6. Calculate ADX (smoothed DX)
        adx = dx.rolling(window=self.window, min_periods=1).mean()
        
        last_adx = self._get_last_value(adx)
        last_plus_di = self._get_last_value(plus_di)
        last_minus_di = self._get_last_value(minus_di)
        
        return last_adx, last_plus_di, last_minus_di

# Convenience instance for default parameters
ADX_CALCULATOR = ADXCalculator()
