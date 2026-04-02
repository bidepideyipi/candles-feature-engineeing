
import pandas as pd

from typing import List, Dict, Any, Tuple

from utils.rsi_calculator import RSI_CALCULATOR
from utils.macd_calculator import MACD_CALCULATOR
from utils.impulse_calculator import IMPULSE_CALCULATOR
from utils.calculator_interface import BaseTechnicalCalculator
from utils.atr_calculator import ATR_CALCULATOR
from utils.stoch_calculator import STOCH_CALCULATOR
from feature.feature_types import Feature15M

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
        self.atr_calculator = ATR_CALCULATOR
        self.stoch_calculator = STOCH_CALCULATOR
        
    def calculate(self, candles15m: List[Dict[str, Any]]) -> Feature15M:
        """
            处理15分钟的特征参数
        Args:
            candles (List[Dict[str, Any]]): 48条数据（因为macd慢线需要48的时间窗口）
            Returns:
            Feature15M: 15分钟特征对象
        """
        close15m = pd.Series(item['close'] for item in candles15m)
        volume15m = pd.Series(item['volume'] for item in candles15m)
        
        rsi_14_15m = int(round(self.rsi_calculator.calculate(close15m), 0))
        macd_line_15m, macd_signal_15m, macd_histogram_15m = self.macd_calculator.calculate(close15m)
        macd_line_15m = round(macd_line_15m, 0)
        macd_signal_15m = round(macd_signal_15m, 0)
        macd_histogram_15m = round(macd_histogram_15m, 3)
        volume_impulse_15m = round(self.vi_calculator.calculate(volume15m), 2)
        
        df15m = pd.DataFrame(candles15m)
        atr_15m = round(self.atr_calculator.calculate(df15m), 0)
        stoch_k_15m, stoch_d_15m = self.stoch_calculator.calculate(df15m)
        stoch_k_15m = round(stoch_k_15m, 0)
        stoch_d_15m = round(stoch_d_15m, 0)
        
        return Feature15M(
            rsi_14_15m=rsi_14_15m,
            volume_impulse_15m=volume_impulse_15m,
            macd_line_15m=macd_line_15m,
            macd_signal_15m=macd_signal_15m,
            macd_histogram_15m=macd_histogram_15m,
            atr_15m=atr_15m,
            stoch_k_15m=stoch_k_15m,
            stoch_d_15m=stoch_d_15m,
        )
    