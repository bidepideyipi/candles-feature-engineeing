
import pandas as pd

from typing import List, Dict, Any

from utils.rsi_calculator import RSI_CALCULATOR
from utils.macd_calculator import MACD_CALCULATOR
from utils.calculator_interface import BaseTechnicalCalculator
from utils.trend_continuation_calulator import TREND_CONTINUATION_CALCULATOR
from utils.atr_calculator import ATR_CALCULATOR
from utils.adx_calculator import ADX_CALCULATOR
from utils.ema_calculator import EMA_12, EMA_26, EMA_48

class Feature4HCreator(BaseTechnicalCalculator):

    """
    FeatureCreator 最小可用版本 只包含一些基本的参数
    - 对于当前的特征计算， float 类型是足够的，不需要改为 Decimal 等类型
    - 如需更高精度，可考虑使用 numpy.float64 ，但通常没有必要
    """
    def __init__(self):
        self.rsi_calculator = RSI_CALCULATOR
        self.macd_calculator = MACD_CALCULATOR
        self.trend_calculator = TREND_CONTINUATION_CALCULATOR
        self.atr_calculator = ATR_CALCULATOR
        self.adx_calculator = ADX_CALCULATOR
        self.ema_12 = EMA_12
        self.ema_26 = EMA_26
        self.ema_48 = EMA_48
        
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
            
        """
        close4H = pd.Series(item['close'] for item in candles4H)
        
        rsi_14_4h = round(self.rsi_calculator.calculate(close4H), 1)  # RSI保留1位小数
        macd_line_4h, macd_signal_4h, _ = self.macd_calculator.calculate(close4H)
        macd_line_4h = round(macd_line_4h, 3)  # MACD保留3位小数
        macd_signal_4h = round(macd_signal_4h, 3)  # MACD信号线保留3位小数
        # 建议4小时趋势延续强度的时间窗口为20~30，这里仍然保留48和MACD慢线时间一致同时看中稳健性
        trend_continuation_4h = round(self.trend_calculator.calculate(close4H), 2)  # 趋势延续强度保留2位小数
        
        ema_12_4h = round(self.ema_12.calculate(close4H), 3)  # 4小时12日均线保留3位小数
        ema_26_4h = round(self.ema_26.calculate(close4H), 3)  # 4小时26日均线保留3位小数
        ema_48_4h = round(self.ema_48.calculate(close4H), 3)  # 4小时48日均线保留3位小数
        
        close4H = pd.Series(item['close'] for item in candles4H)
        high4H = pd.Series(item['high'] for item in candles4H)
        low4H = pd.Series(item['low'] for item in candles4H)    
        df = pd.DataFrame({'high': high4H, 'low': low4H, 'close': close4H})
        
        atr_4h = round(self.atr_calculator.calculate(df), 3)  # 4小时波动率保留3位小数
        
        adx_value, plus_di, minus_di = self.adx_calculator.calculate(df)
        adx_4h = round(adx_value, 1)  # 4小时趋势强度保留1位小数
        plus_di_4h = round(plus_di, 1)  # 4小时上涨方向指标保留1位小数
        minus_di_4h = round(minus_di, 1)  # 4小时下跌方向指标保留1位小数
        return {
            "rsi_14_4h": rsi_14_4h,
            "trend_continuation_4h": trend_continuation_4h,
            "macd_line_4h": macd_line_4h,
            "macd_signal_4h": macd_signal_4h,
            "atr_4h": atr_4h,
            "adx_4h": adx_4h,
            "plus_di_4h": plus_di_4h,
            "minus_di_4h": minus_di_4h,
            "ema_12_4h": ema_12_4h,
            "ema_26_4h": ema_26_4h,
            "ema_48_4h": ema_48_4h,
        }
    