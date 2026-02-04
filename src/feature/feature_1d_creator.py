
import pandas as pd

from typing import List, Dict, Any

from utils.rsi_calculator import RSI_CALCULATOR
from utils.atr_calculator import ATR_CALCULATOR
from utils.calculator_interface import BaseTechnicalCalculator

class Feature1DCreator(BaseTechnicalCalculator):

    """
    FeatureCreator 最小可用版本 只包含一些基本的参数
    - 对于当前的特征计算， float 类型是足够的，不需要改为 Decimal 等类型
    - 如需更高精度，可考虑使用 numpy.float64 ，但通常没有必要
    """
    def __init__(self):
        self.rsi_calculator = RSI_CALCULATOR
        self.atr_calculator = ATR_CALCULATOR
        
    def calculate(self, candles1D: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
            处理一天的特征参数
        Args:
            candles1D (List[Dict[str, Any]]): 1天数据（因为atr需要1天的时间窗口）
            Returns:
            Dict[str, Any]:
            
            rsi_14_1d       # 日线动量
            atr_1d          # 日线波动率
            
        """
        close1D = pd.Series(item['close'] for item in candles1D)
        high1D = pd.Series(item['high'] for item in candles1D)
        low1D = pd.Series(item['low'] for item in candles1D)
        df = pd.DataFrame({'high': high1D, 'low': low1D, 'close': close1D})
        
        rsi_14_1d = round(self.rsi_calculator.calculate(close1D), 0)  # RSI保留0位小数
        atr_1d = round(self.atr_calculator.calculate(df), 3)  # ATR保留3位小数
        
        return {
            "rsi_14_1d": rsi_14_1d,
            "atr_1d": atr_1d,
        }
    