"""
RSI Divergence Calculator
Detects RSI divergence patterns between price and RSI indicator
"""

import pandas as pd
import numpy as np
from typing import Union, Tuple
from .calculator_interface import BaseTechnicalCalculator
from .rsi_calculator import RSI_CALCULATOR

class RSIDivergenceDetector(BaseTechnicalCalculator):
    """
    RSI背离检测器
    检测价格与RSI指标之间的背离信号
    
    返回值:
        1: 看涨背离（价格新低但RSI未新低）
        -1: 看跌背离（价格新高但RSI未新高）
        0: 无背离
    """
    
    def __init__(self, window: int = 14, lookback: int = 20, min_strength: float = 0.1):
        """
        初始化RSI背离检测器
        
        Args:
            window: RSI计算周期（默认：14）
            lookback: 回溯窗口大小，用于检测极值点（默认：20）
            min_strength: 最小背离强度，避免虚假信号（默认：0.1）
        """
        self.window = window
        self.lookback = lookback
        self.min_strength = min_strength
        self.rsi_calculator = RSI_CALCULATOR
    
    def calculate(self, close_prices: Union[pd.Series, list, np.ndarray]) -> int:
        """
        检测RSI背离信号
        
        Args:
            close_prices: 收盘价序列
            
        Returns:
            int: 背离信号 (1: 看涨背离, -1: 看跌背离, 0: 无背离)
        """
        # 转换为pandas Series
        prices_series = self._convert_to_series(close_prices)
        
        # 数据不足时返回无背离
        if len(prices_series) < self.lookback * 2:
            return 0
        
        # 计算RSI值
        rsi_values = self._calculate_rsi_series(prices_series)
        
        # 如果RSI数据不足，返回无背离
        if len(rsi_values) < self.lookback * 2:
            return 0
        
        # 检测看跌背离（价格新高但RSI未新高）
        bearish_divergence = self._detect_bearish_divergence(prices_series, rsi_values)
        if bearish_divergence:
            return -1
        
        # 检测看涨背离（价格新低但RSI未新低）
        bullish_divergence = self._detect_bullish_divergence(prices_series, rsi_values)
        if bullish_divergence:
            return 1
        
        return 0
    
    def _calculate_rsi_series(self, prices: pd.Series) -> pd.Series:
        """
        计算完整的RSI序列
        
        Args:
            prices: 价格序列
            
        Returns:
            RSI值序列
        """
        # 计算价格变化
        delta = prices.diff()
        
        # 分离涨跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 计算平均涨跌
        avg_gain = gain.rolling(window=self.window, min_periods=1).mean()
        avg_loss = loss.rolling(window=self.window, min_periods=1).mean()
        
        # 避免除零
        avg_loss = avg_loss.replace(0, 1)
        
        # 计算RS和RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # 处理无穷值
        rsi = rsi.replace([np.inf, -np.inf], np.nan)
        
        return rsi
    
    def _detect_bearish_divergence(self, prices: pd.Series, rsi_values: pd.Series) -> bool:
        """
        检测看跌背离（价格新高但RSI未新高）
        
        Args:
            prices: 价格序列
            rsi_values: RSI值序列
            
        Returns:
            bool: 是否存在看跌背离
        """
        # 获取最近的价格和RSI
        recent_prices = prices.iloc[-self.lookback:]
        recent_rsi = rsi_values.iloc[-self.lookback:]
        
        # 查找价格的局部高点
        price_peaks = self._find_peaks(recent_prices)
        if len(price_peaks) < 2:
            return False
        
        # 查找RSI的局部高点
        rsi_peaks = self._find_peaks(recent_rsi)
        if len(rsi_peaks) < 2:
            return False
        
        # 获取最近两个价格高点
        last_price_peak_idx = price_peaks[-1]
        prev_price_peak_idx = price_peaks[-2]
        
        last_price_peak = prices.iloc[last_price_peak_idx]
        prev_price_peak = prices.iloc[prev_price_peak_idx]
        
        # 获取对应位置的RSI值
        last_rsi_peak = rsi_values.iloc[last_price_peak_idx]
        prev_rsi_peak = rsi_values.iloc[prev_price_peak_idx]
        
        # 检查是否形成背离
        # 价格创新高，但RSI未创新高，且背离强度足够
        price_makes_new_high = last_price_peak > prev_price_peak
        rsi_does_not_make_new_high = last_rsi_peak <= prev_rsi_peak
        divergence_strength = (prev_rsi_peak - last_rsi_peak) / prev_rsi_peak
        
        is_bearish_divergence = (
            price_makes_new_high and 
            rsi_does_not_make_new_high and 
            divergence_strength >= self.min_strength
        )
        
        return is_bearish_divergence
    
    def _detect_bullish_divergence(self, prices: pd.Series, rsi_values: pd.Series) -> bool:
        """
        检测看涨背离（价格新低但RSI未新低）
        
        Args:
            prices: 价格序列
            rsi_values: RSI值序列
            
        Returns:
            bool: 是否存在看涨背离
        """
        # 获取最近的价格和RSI
        recent_prices = prices.iloc[-self.lookback:]
        recent_rsi = rsi_values.iloc[-self.lookback:]
        
        # 查找价格的局部低点
        price_troughs = self._find_troughs(recent_prices)
        if len(price_troughs) < 2:
            return False
        
        # 查找RSI的局部低点
        rsi_troughs = self._find_troughs(recent_rsi)
        if len(rsi_troughs) < 2:
            return False
        
        # 获取最近两个价格低点
        last_price_trough_idx = price_troughs[-1]
        prev_price_trough_idx = price_troughs[-2]
        
        last_price_trough = prices.iloc[last_price_trough_idx]
        prev_price_trough = prices.iloc[prev_price_trough_idx]
        
        # 获取对应位置的RSI值
        last_rsi_trough = rsi_values.iloc[last_price_trough_idx]
        prev_rsi_trough = rsi_values.iloc[prev_price_trough_idx]
        
        # 检查是否形成背离
        # 价格创新低，但RSI未创新低，且背离强度足够
        price_makes_new_low = last_price_trough < prev_price_trough
        rsi_does_not_make_new_low = last_rsi_trough >= prev_rsi_trough
        divergence_strength = (last_rsi_trough - prev_rsi_trough) / prev_rsi_trough
        
        is_bullish_divergence = (
            price_makes_new_low and 
            rsi_does_not_make_new_low and 
            divergence_strength >= self.min_strength
        )
        
        return is_bullish_divergence
    
    def _find_peaks(self, data: pd.Series, window: int = 5) -> list:
        """
        查找局部极值点（波峰）
        
        Args:
            data: 数据序列
            window: 检查窗口大小
            
        Returns:
            list: 波峰索引列表
        """
        peaks = []
        for i in range(window, len(data) - window):
            current = data.iloc[i]
            # 检查是否为局部最大值
            if all(current >= data.iloc[i - window:i]) and all(current >= data.iloc[i + 1:i + window + 1]):
                peaks.append(i)
        return peaks
    
    def _find_troughs(self, data: pd.Series, window: int = 5) -> list:
        """
        查找局部极值点（波谷）
        
        Args:
            data: 数据序列
            window: 检查窗口大小
            
        Returns:
            list: 波谷索引列表
        """
        troughs = []
        for i in range(window, len(data) - window):
            current = data.iloc[i]
            # 检查是否为局部最小值
            if all(current <= data.iloc[i - window:i]) and all(current <= data.iloc[i + 1:i + window + 1]):
                troughs.append(i)
        return troughs
    
    def get_divergence_details(self, close_prices: Union[pd.Series, list, np.ndarray]) -> dict:
        """
        获取背离检测的详细信息
        
        Args:
            close_prices: 收盘价序列
            
        Returns:
            dict: 包含背离详细信息的字典
        """
        prices_series = self._convert_to_series(close_prices)
        
        if len(prices_series) < self.lookback * 2:
            return {
                'signal': 0,
                'type': None,
                'strength': 0.0,
                'message': '数据不足'
            }
        
        rsi_values = self._calculate_rsi_series(prices_series)
        recent_prices = prices_series.iloc[-self.lookback:]
        recent_rsi = rsi_values.iloc[-self.lookback:]
        
        # 检测看跌背离
        if self._detect_bearish_divergence(prices_series, rsi_values):
            price_peaks = self._find_peaks(recent_prices)
            rsi_peaks = self._find_peaks(recent_rsi)
            
            if len(price_peaks) >= 2 and len(rsi_peaks) >= 2:
                last_price_peak_idx = price_peaks[-1]
                prev_price_peak_idx = price_peaks[-2]
                
                last_price = prices_series.iloc[last_price_peak_idx]
                prev_price = prices_series.iloc[prev_price_peak_idx]
                last_rsi = rsi_values.iloc[last_price_peak_idx]
                prev_rsi = rsi_values.iloc[prev_price_peak_idx]
                
                strength = (prev_rsi - last_rsi) / prev_rsi if prev_rsi != 0 else 0
                
                return {
                    'signal': -1,
                    'type': 'bearish',
                    'strength': round(strength, 4),
                    'message': f'看跌背离: 价格({last_price:.2f})创新高但RSI({last_rsi:.2f})未创新高',
                    'last_price': round(last_price, 2),
                    'prev_price': round(prev_price, 2),
                    'last_rsi': round(last_rsi, 2),
                    'prev_rsi': round(prev_rsi, 2)
                }
        
        # 检测看涨背离
        if self._detect_bullish_divergence(prices_series, rsi_values):
            price_troughs = self._find_troughs(recent_prices)
            rsi_troughs = self._find_troughs(recent_rsi)
            
            if len(price_troughs) >= 2 and len(rsi_troughs) >= 2:
                last_price_trough_idx = price_troughs[-1]
                prev_price_trough_idx = price_troughs[-2]
                
                last_price = prices_series.iloc[last_price_trough_idx]
                prev_price = prices_series.iloc[prev_price_trough_idx]
                last_rsi = rsi_values.iloc[last_price_trough_idx]
                prev_rsi = rsi_values.iloc[prev_price_trough_idx]
                
                strength = (last_rsi - prev_rsi) / prev_rsi if prev_rsi != 0 else 0
                
                return {
                    'signal': 1,
                    'type': 'bullish',
                    'strength': round(strength, 4),
                    'message': f'看涨背离: 价格({last_price:.2f})创新低但RSI({last_rsi:.2f})未创新低',
                    'last_price': round(last_price, 2),
                    'prev_price': round(prev_price, 2),
                    'last_rsi': round(last_rsi, 2),
                    'prev_rsi': round(prev_rsi, 2)
                }
        
        return {
            'signal': 0,
            'type': None,
            'strength': 0.0,
            'message': '无背离'
        }


# 全局实例
RSI_DIVERGENCE_DETECTOR = RSIDivergenceDetector()