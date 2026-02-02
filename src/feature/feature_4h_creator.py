
import pandas as pd

from typing import List, Dict, Any

from utils.rsi_calculator import RSI_CALCULATOR
from utils.macd_calculator import MACD_CALCULATOR
from utils.calculator_interface import BaseTechnicalCalculator
from utils.trend_continuation_calulator import TREND_CONTINUATION_CALCULATOR

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
            
        """
        close4H = pd.Series(item['close'] for item in candles4H)
        
        rsi_14_4h = round(self.rsi_calculator.calculate(close4H), 1)  # RSI保留1位小数
        macd_line_4h, macd_signal_4h, _ = self.macd_calculator.calculate(close4H)
        macd_line_4h = round(macd_line_4h, 3)  # MACD保留3位小数
        macd_signal_4h = round(macd_signal_4h, 3)  # MACD信号线保留3位小数
        # 建议4小时趋势延续强度的时间窗口为20~30，这里仍然保留48和MACD慢线时间一致同时看中稳健性
        trend_continuation_4h = round(self.trend_calculator.calculate(close4H), 2)  # 趋势延续强度保留2位小数
        
        return {
            "rsi_14_4h": rsi_14_4h,
            "trend_continuation_4h": trend_continuation_4h,
            "macd_line_4h": macd_line_4h,
            "macd_signal_4h": macd_signal_4h
        }
    