
import pandas as pd

from typing import List, Dict, Any

from utils.rsi_calculator import RSI_CALCULATOR
from utils.macd_calculator import MACD_CALCULATOR
from utils.calculator_interface import BaseTechnicalCalculator
from utils.trend_continuation_calulator import TREND_CONTINUATION_CALCULATOR
from utils.atr_calculator import ATR_CALCULATOR
from utils.adx_calculator import ADX_CALCULATOR
from utils.ema_calculator import EMA_12, EMA_26, EMA_48, EMACrossoverSignal
from utils.pinbar_calculator import PINBAR_CALCULATOR

class Feature4HCreator(BaseTechnicalCalculator):

    """
    FeatureCreator 最小可用版本 只包含一些基本的参数
    - 对于当前的特征计算， float 类型是足够的，不需要改为 Decimal 等类型
    - 如需更高精度，可考虑使用 numpy.float64 ，但通常没有必要
    """
    def __init__(self, close_mean: float, close_std: float):
        self.rsi_calculator = RSI_CALCULATOR
        self.macd_calculator = MACD_CALCULATOR
        self.trend_calculator = TREND_CONTINUATION_CALCULATOR
        self.atr_calculator = ATR_CALCULATOR
        self.adx_calculator = ADX_CALCULATOR
        self.ema_12 = EMA_12
        self.ema_26 = EMA_26
        self.ema_48 = EMA_48
        self.pinbar_calculator = PINBAR_CALCULATOR
        self.close_mean = close_mean
        self.close_std = close_std
        
    def calculate(self, candles4H: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
            处理一小时的特征参数
        Args:
            candles4H (List[Dict[str, Any]]): 48条数据（因为macd慢线需要48的时间窗口）
            Returns:
            Dict[str, Any]:
            
            4小时中期特征
            "rsi_14_4h": Number,              // 4小时RSI
            "trend_continuation_4h": Number   // 4小时趋势延续强度
            "macd_line_4h": Number,           // MACD快线
            "macd_signal_4h": Number,         // MACD信号线
            "atr_4h": Number,                 // 4小时波动率（新增）
            "adx_4h": Number,                 // 4小时趋势强度（新增）
            "ema_12_4h": Number,             // 4小时12日均线（新增）
            "ema_26_4h": Number,             // 4小时26日均线（新增）
            "ema_48_4h": Number              // 4小时48日均线（新增）
            "ema_cross_4h_12_26": Number           // EMA交叉信号（12 vs 26, 26 vs 48）
            "ema_cross_4h_26_48": Number           // EMA交叉信号（26 vs 48）
            
        """
        close4H = pd.Series(item['close'] for item in candles4H)
        
        rsi_14_4h = round(self.rsi_calculator.calculate(close4H), 1)  # RSI保留1位小数
        macd_line_4h, macd_signal_4h, macd_histogram_4h = self.macd_calculator.calculate(close4H)
        macd_line_4h = round(macd_line_4h, 0)  # MACD保留0位小数
        macd_signal_4h = round(macd_signal_4h, 0)  # MACD信号线保留0位小数
        macd_histogram_4h = round(macd_histogram_4h, 3)  # MACD直方图保留3位小数
        
        # 建议4小时趋势延续强度的时间窗口为20~30，这里仍然保留48和MACD慢线时间一致同时看中稳健性
        trend_continuation_4h = round(self.trend_calculator.calculate(close4H), 2)  # 趋势延续强度保留2位小数
        
        ema_12_4h = self.ema_12.calculate(close4H)  # 4小时12日均线
        ema_26_4h = self.ema_26.calculate(close4H)  # 4小时26日均线
        ema_48_4h = self.ema_48.calculate(close4H)  # 4小时48日均线
        ema_12_4h = round((ema_12_4h - self.close_mean) / self.close_std, 3)  # 价格标准化保留3位小数
        ema_26_4h = round((ema_26_4h - self.close_mean) / self.close_std, 3)  # 价格标准化保留3位小数
        ema_48_4h = round((ema_48_4h - self.close_mean) / self.close_std, 3)  # 价格标准化保留3位小数
        
        high4H = pd.Series(item['high'] for item in candles4H)
        low4H = pd.Series(item['low'] for item in candles4H)
        open4H = pd.Series(item['open'] for item in candles4H)
        df = pd.DataFrame({'high': high4H, 'low': low4H, 'open': open4H, 'close': close4H})
        
        atr_4h = round(self.atr_calculator.calculate(df), 0)  # 4小时波动率保留3位小数
        
        adx_value, plus_di, minus_di = self.adx_calculator.calculate(df)
        adx_4h = round(adx_value, 1)  # 4小时趋势强度保留1位小数
        plus_di_4h = round(plus_di, 1)  # 4小时上涨方向指标保留1位小数
        minus_di_4h = round(minus_di, 1)  # 4小时下跌方向指标保留1位小数
        
        ema_cross_4h_12_26 = EMACrossoverSignal.calculate_from_values(ema_12_4h, ema_26_4h)
        ema_cross_4h_26_48 = EMACrossoverSignal.calculate_from_values(ema_26_4h, ema_48_4h)
        
        pinbar_features = self.pinbar_calculator.calculate(
            high_prices=df['high'],
            low_prices=df['low'],
            open_prices=df['open'],
            close_prices=df['close']
        )
        
        return {
            "rsi_14_4h": rsi_14_4h,
            "trend_continuation_4h": trend_continuation_4h,
            "macd_line_4h": macd_line_4h,
            "macd_signal_4h": macd_signal_4h,
            "macd_histogram_4h": macd_histogram_4h,
            "atr_4h": atr_4h,
            "adx_4h": adx_4h,
            "plus_di_4h": plus_di_4h,
            "minus_di_4h": minus_di_4h,
            "ema_12_4h": ema_12_4h,
            "ema_26_4h": ema_26_4h,
            "ema_48_4h": ema_48_4h,
            "ema_cross_4h_12_26": ema_cross_4h_12_26,
            "ema_cross_4h_26_48": ema_cross_4h_26_48,
            "upper_shadow_ratio_4h": round(pinbar_features['upper_shadow_ratio'], 2),
            "lower_shadow_ratio_4h": round(pinbar_features['lower_shadow_ratio'], 2),
            "shadow_imbalance_4h": round(pinbar_features['shadow_imbalance'], 2),
            "body_ratio_4h": round(pinbar_features['body_ratio'], 2),
        }
    