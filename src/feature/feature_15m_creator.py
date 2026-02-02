
import pandas as pd

from typing import List, Dict, Any, Tuple

from utils.rsi_calculator import RSI_CALCULATOR
from utils.macd_calculator import MACD_CALCULATOR
from utils.impulse_calculator import IMPULSE_CALCULATOR
from utils.calculator_interface import BaseTechnicalCalculator

class Feature15mCreator(BaseTechnicalCalculator):

    """
    FeatureCreator 最小可用版本 只包含一些基本的参数
    - 对于当前的特征计算， float 类型是足够的，不需要改为 Decimal 等类型
    - 如需更高精度，可考虑使用 numpy.float64 ，但通常没有必要
    """
    def __init__(self):
        self.rsi_calculator = RSI_CALCULATOR
        self.macd_calculator = MACD_CALCULATOR
        self.vi_calculator = IMPULSE_CALCULATOR
        
    def calculate(self, candles15m: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
            处理一小时的特征参数
        Args:
            candles (List[Dict[str, Any]]): 48条数据（因为macd慢线需要48的时间窗口）
            Returns:
            Dict[str, Any]:
            
            15分钟高频特征
            "rsi_14_15m": Number,             // 15分钟RSI
            "volume_impulse_15m": Number,     // 15分钟成交量脉冲
            "macd_line_15m": Number,           // MACD快线
            "macd_signal_15m": Number,         // MACD信号线
            
        """
        close15m = pd.Series(item['close'] for item in candles15m)
        volume15m = pd.Series(item['volume'] for item in candles15m)
        
        rsi_14_15m = round(self.rsi_calculator.calculate(close15m), 1)  # RSI保留1位小数
        macd_line_15m, macd_signal_15m, _ = self.macd_calculator.calculate(close15m)
        macd_line_15m = round(macd_line_15m, 3)  # MACD保留3位小数
        macd_signal_15m = round(macd_signal_15m, 3)  # MACD信号线保留3位小数
        volume_impulse_15m = round(self.vi_calculator.calculate(volume15m), 2)  # 成交量脉冲保留2位小数
        
        return {
            "rsi_14_15m": rsi_14_15m,
            "volume_impulse_15m": volume_impulse_15m,
            "macd_line_15m": macd_line_15m,
            "macd_signal_15m": macd_signal_15m
        }
    