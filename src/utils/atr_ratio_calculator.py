"""
ATR Ratio Calculator
Calculates ATR ratios between different timeframes and periods
"""

import pandas as pd
import numpy as np
from typing import Union, Tuple
from .calculator_interface import BaseTechnicalCalculator
from .atr_calculator import ATR_CALCULATOR

class ATRRatioCalculator(BaseTechnicalCalculator):
    """
    ATR比值计算器
    
    用于计算不同周期、不同时间框架之间的ATR比值，捕捉波动率变化模式
    
    功能：
    - 多周期ATR比值（4H/1H, 1H/15M等）
    - ATR动量（变化率）
    - ATR分位数（历史分位数）
    - 波动率扩张/收缩检测
    """
    
    def __init__(self, 
                 short_period: int = 12, 
                 long_period: int = 24, 
                 lookback_window: int = 48):
        """
        初始化ATR比值计算器
        
        Args:
            short_period: 短期ATR周期（默认：12）
            long_period: 长期ATR周期（默认：24）
            lookback_window: 回溯窗口大小，用于分位数计算（默认：48）
            
        数据点要求:
            - 最少需要: long_period * 2 = 48个数据点
            - 与系统统一数据点数保持一致
            - 参数比例: short_period : long_period = 1 : 2
        """
        self.short_period = short_period
        self.long_period = long_period
        self.lookback_window = lookback_window
        self.atr_calculator = ATR_CALCULATOR
    
    def calculate(self, df: Union[pd.DataFrame, dict]) -> float:
        """
        计算ATR比值（短期ATR / 长期ATR）
        
        Args:
            df: DataFrame with OHLC data containing 'high', 'low', 'close' columns
            
        Returns:
            float: ATR比值
        """
        # 验证数据格式
        if isinstance(df, dict):
            df = pd.DataFrame([df])
        
        # 验证所需列
        required_cols = ['high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")
        
        # 确保有足够的数据
        if len(df) < self.long_period * 2:
            raise ValueError(f"需要至少{self.long_period * 2}个数据点来计算ATR比值")
        
        # 计算完整ATR序列
        atr_series = self._calculate_atr_series(df)
        
        # 计算短期和长期ATR
        short_atr = atr_series.iloc[-self.short_period:].mean()
        long_atr = atr_series.iloc[-self.long_period:].mean()
        
        # 避免除零
        if long_atr == 0:
            return 0.0
        
        # 计算比值
        ratio = short_atr / long_atr
        
        return float(ratio)
    
    def calculate_cross_timeframe_ratio(self, 
                                        short_df: pd.DataFrame, 
                                        long_df: pd.DataFrame) -> float:
        """
        计算跨时间框架ATR比值
        
        Args:
            short_df: 短周期数据（如1H）
            long_df: 长周期数据（如4H）
            
        Returns:
            float: 跨周期ATR比值
        """
        # 计算两个周期的ATR
        short_atr = self.atr_calculator.calculate(short_df)
        long_atr = self.atr_calculator.calculate(long_df)
        
        # 避免除零
        if long_atr == 0:
            return 0.0
        
        # 计算比值
        ratio = short_atr / long_atr
        
        return float(ratio)
    
    def calculate_momentum(self, df: pd.DataFrame) -> float:
        """
        计算ATR动量（ATR变化率）
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            float: ATR动量值
        """
        # 计算ATR序列
        atr_series = self._calculate_atr_series(df)
        
        if len(atr_series) < 2:
            return 0.0
        
        # 计算变化率
        current_atr = atr_series.iloc[-1]
        prev_atr = atr_series.iloc[-2]
        
        if prev_atr == 0:
            return 0.0
        
        momentum = (current_atr - prev_atr) / prev_atr
        
        return float(momentum)
    
    def calculate_percentile(self, df: pd.DataFrame) -> float:
        """
        计算当前ATR在历史分位数中的位置
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            float: ATR分位数（0-1之间）
        """
        # 计算ATR序列
        atr_series = self._calculate_atr_series(df)
        
        if len(atr_series) < self.lookback_window:
            return 0.5  # 数据不足时返回中位数
        
        # 获取回溯窗口内的ATR值
        recent_atr_values = atr_series.iloc[-self.lookback_window:].values
        
        # 计算当前ATR在历史中的分位数
        current_atr = atr_series.iloc[-1]
        percentile = (recent_atr_values < current_atr).sum() / len(recent_atr_values)
        
        return float(percentile)
    
    def detect_volatility_expansion(self, df: pd.DataFrame, threshold: float = 1.5) -> int:
        """
        检测波动率扩张
        
        Args:
            df: DataFrame with OHLC data
            threshold: 扩张阈值（默认：1.5，即ATR超过均值50%）
            
        Returns:
            int: 1=扩张, 0=正常
        """
        # 计算ATR序列
        atr_series = self._calculate_atr_series(df)
        
        if len(atr_series) < self.lookback_window:
            return 0
        
        # 计算历史ATR均值
        historical_atr_values = atr_series.iloc[-self.lookback_window:].values
        mean_atr = historical_atr_values.mean()
        
        if mean_atr == 0:
            return 0
        
        # 检测扩张
        current_atr = atr_series.iloc[-1]
        if current_atr > threshold * mean_atr:
            return 1
        
        return 0
    
    def detect_volatility_contraction(self, df: pd.DataFrame, threshold: float = 0.7) -> int:
        """
        检测波动率收缩
        
        Args:
            df: DataFrame with OHLC data
            threshold: 收缩阈值（默认：0.7，即ATR低于均值30%）
            
        Returns:
            int: 1=收缩, 0=正常
        """
        # 计算ATR序列
        atr_series = self._calculate_atr_series(df)
        
        if len(atr_series) < self.lookback_window:
            return 0
        
        # 计算历史ATR均值
        historical_atr_values = atr_series.iloc[-self.lookback_window:].values
        mean_atr = historical_atr_values.mean()
        
        if mean_atr == 0:
            return 0
        
        # 检测收缩
        current_atr = atr_series.iloc[-1]
        if current_atr < threshold * mean_atr:
            return 1
        
        return 0
    
    def _calculate_atr_series(self, df: pd.DataFrame) -> pd.Series:
        """
        计算完整的ATR序列
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            pd.Series: ATR值序列
        """
        # 转换为float类型
        high_prices = df['high'].astype(float)
        low_prices = df['low'].astype(float)
        close_prices = df['close'].astype(float)
        
        # 计算真实波幅
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
        
        # 计算ATR序列
        tr_series = pd.Series(tr_list)
        
        # 前期使用简单移动平均
        sma_atr = tr_series.rolling(window=14).mean()
        
        # 后期使用EMA平滑
        atr = sma_atr.copy()
        for i in range(14, len(tr_series)):
            atr.iloc[i] = (tr_series.iloc[i] + 13 * atr.iloc[i-1]) / 14
        
        return atr
    
    def get_volatility_profile(self, df: pd.DataFrame) -> dict:
        """
        获取完整的波动率分析报告
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            dict: 波动率分析报告
        """
        try:
            atr_series = self._calculate_atr_series(df)
            
            if len(atr_series) < self.lookback_window:
                return {
                    'status': 'insufficient_data',
                    'message': f'需要至少{self.lookback_window}个数据点'
                }
            
            current_atr = atr_series.iloc[-1]
            recent_atr_values = atr_series.iloc[-self.lookback_window:].values
            
            return {
                'status': 'success',
                'current_atr': float(current_atr),
                'atr_momentum': self.calculate_momentum(df),
                'atr_percentile': self.calculate_percentile(df),
                'volatility_expansion': self.detect_volatility_expansion(df),
                'volatility_contraction': self.detect_volatility_contraction(df),
                'atr_ratio_short_long': self.calculate(df),
                'historical_stats': {
                    'mean': float(recent_atr_values.mean()),
                    'std': float(recent_atr_values.std()),
                    'min': float(recent_atr_values.min()),
                    'max': float(recent_atr_values.max())
                }
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }


# 全局实例
ATR_RATIO_CALCULATOR = ATRRatioCalculator()