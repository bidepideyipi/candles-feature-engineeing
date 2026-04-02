
import pandas as pd
import numpy as np
from typing import List, Dict, Any

from utils.rsi_calculator import RSI_CALCULATOR
from utils.macd_calculator import MACD_CALCULATOR
from utils.pinbar_calculator import PINBAR_CALCULATOR
from utils.calculator_interface import BaseTechnicalCalculator
from utils.trend_continuation_calulator import TREND_CONTINUATION_CALCULATOR
from utils.atr_calculator import ATR_CALCULATOR
from utils.adx_calculator import ADX_CALCULATOR
from utils.ema_calculator import EMA_12, EMA_26, EMA_48, EMACrossoverSignal
from feature.feature_types import Feature1H

class Feature1HCreator(BaseTechnicalCalculator):

    """
    FeatureCreator 最小可用版本 只包含一些基本的参数
    - 对于当前的特征计算， float 类型是足够的，不需要改为 Decimal 等类型
    - 如需更高精度，可考虑使用 numpy.float64 ，但通常没有必要
    """
    def __init__(self, close_mean: float, close_std: float, vol_mean: float, vol_std: float):
        self.rsi_calculator = RSI_CALCULATOR
        self.macd_calculator = MACD_CALCULATOR
        self.pinbar_calculator = PINBAR_CALCULATOR
        self.close_mean = close_mean
        self.close_std = close_std
        self.vol_mean = vol_mean
        self.vol_std = vol_std
        self.trend_calculator = TREND_CONTINUATION_CALCULATOR
        self.atr_calculator = ATR_CALCULATOR
        self.adx_calculator = ADX_CALCULATOR
        self.ema_12 = EMA_12
        self.ema_26 = EMA_26
        self.ema_48 = EMA_48
        
        
    def calculate(self, candles1h: List[Dict[str, Any]]) -> Feature1H:
        """
            处理一小时的特征参数
        Args:
            candles (List[Dict[str, Any]]): 48条数据（因为macd慢线需要48的时间窗口）
            Returns:
            Feature1H: 1小时特征对象
        """
        close1h = pd.Series(item['close'] for item in candles1h)
        volume1h = pd.Series(item['volume'] for item in candles1h)
        
        close_1h_normalized = round((close1h.iloc[-1] - self.close_mean) / self.close_std, 3)
        volume_1h_normalized = round((volume1h.iloc[-1] - self.vol_mean) / self.vol_std, 3)
        
        rsi_14_1h = int(round(self.rsi_calculator.calculate(close1h), 0))
        macd_line_1h, macd_signal_1h, macd_histogram_1h = self.macd_calculator.calculate(close1h)
        macd_line_1h = round(macd_line_1h, 0)
        macd_signal_1h = round(macd_signal_1h, 0)
        macd_histogram_1h = round(macd_histogram_1h, 3)
        
        high1h = pd.Series(item['high'] for item in candles1h)
        low1h = pd.Series(item['low'] for item in candles1h)
        open1h = pd.Series(item['open'] for item in candles1h)
        df = pd.DataFrame({'high': high1h, 'low': low1h, 'open': open1h, 'close': close1h})
        
        atr_1h = round(self.atr_calculator.calculate(df), 0)
        
        adx_value, plus_di, minus_di = self.adx_calculator.calculate(df)
        adx_1h = round(adx_value, 1)
        plus_di_1h = round(plus_di, 1)
        minus_di_1h = round(minus_di, 1)
        
        ema_12_1h = self.ema_12.calculate(close1h)
        ema_26_1h = self.ema_26.calculate(close1h)
        ema_48_1h = self.ema_48.calculate(close1h)
        ema_12_1h = round((ema_12_1h - self.close_mean) / self.close_std, 3)
        ema_26_1h = round((ema_26_1h - self.close_mean) / self.close_std, 3)
        ema_48_1h = round((ema_48_1h - self.close_mean) / self.close_std, 3)
        
        ema_cross_1h_12_26 = EMACrossoverSignal.calculate_from_values(ema_12_1h, ema_26_1h)
        ema_cross_1h_26_48 = EMACrossoverSignal.calculate_from_values(ema_26_1h, ema_48_1h)
        
        last_record = candles1h[-1]
        record_hour = last_record['record_hour']
        day_of_week = last_record['day_of_week']
        hour_rad = record_hour * (2 * np.pi / 24)
        hour_cos = round(np.cos(hour_rad), 4)
        hour_sin = round(np.sin(hour_rad), 4)
        
        pinbar_features = self.pinbar_calculator.calculate(
            pd.Series(item['high'] for item in candles1h),
            pd.Series(item['low'] for item in candles1h),
            pd.Series(item['open'] for item in candles1h),
            pd.Series(item['close'] for item in candles1h)
        )
        
        return Feature1H(
            close_1h_normalized=close_1h_normalized,
            volume_1h_normalized=volume_1h_normalized,
            rsi_14_1h=rsi_14_1h,
            macd_line_1h=macd_line_1h,
            macd_signal_1h=macd_signal_1h,
            macd_histogram_1h=macd_histogram_1h,
            price=close1h.iloc[-1],
            hour_cos=hour_cos,
            hour_sin=hour_sin,
            day_of_week=day_of_week,
            upper_shadow_ratio_1h=round(pinbar_features['upper_shadow_ratio'], 2),
            lower_shadow_ratio_1h=round(pinbar_features['lower_shadow_ratio'], 2),
            shadow_imbalance_1h=round(pinbar_features['shadow_imbalance'], 2),
            body_ratio_1h=round(pinbar_features['body_ratio'], 2),
            atr_1h=atr_1h,
            adx_1h=adx_1h,
            plus_di_1h=plus_di_1h,
            minus_di_1h=minus_di_1h,
            ema_12_1h=ema_12_1h,
            ema_26_1h=ema_26_1h,
            ema_48_1h=ema_48_1h,
            ema_cross_1h_12_26=ema_cross_1h_12_26,
            ema_cross_1h_26_48=ema_cross_1h_26_48,
        )
    