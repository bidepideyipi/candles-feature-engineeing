
import pandas as pd

from typing import List, Dict, Any

from utils.rsi_calculator import RSI_CALCULATOR
from utils.atr_calculator import ATR_CALCULATOR
from utils.calculator_interface import BaseTechnicalCalculator
from utils.bollinger_bands_calculator import BOLLINGER_BANDS_20
from utils.pinbar_calculator import PINBAR_CALCULATOR

class Feature1DCreator(BaseTechnicalCalculator):

    """
    FeatureCreator 最小可用版本 只包含一些基本的参数
    - 对于当前的特征计算， float 类型是足够的，不需要改为 Decimal 等类型
    - 如需更高精度，可考虑使用 numpy.float64 ，但通常没有必要
    """
    def __init__(self, close_mean: float, close_std: float):
        self.rsi_calculator = RSI_CALCULATOR
        self.atr_calculator = ATR_CALCULATOR
        self.bollinger_calculator = BOLLINGER_BANDS_20
        self.pinbar_calculator = PINBAR_CALCULATOR
        self.close_mean = close_mean
        self.close_std = close_std
        
    def calculate(self, candles1D: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
            处理一天的特征参数
        Args:
            candles1D (List[Dict[str, Any]]): 1天数据（因为atr需要1天的时间窗口）
            Returns:
            Dict[str, Any]:
            
            rsi_14_1d       # 日线动量
            atr_1d          # 日线波动率
            bollinger_upper_1d  # 布林带上轨
            bollinger_lower_1d  # 布林带下轨
            bollinger_position_1d  # 布林带位置（价格在带内的相对位置）
            
        """
        close1D = pd.Series(item['close'] for item in candles1D)
        high1D = pd.Series(item['high'] for item in candles1D)
        low1D = pd.Series(item['low'] for item in candles1D)
        open1D = pd.Series(item['open'] for item in candles1D)
        df = pd.DataFrame({'high': high1D, 'low': low1D, 'open': open1D, 'close': close1D})
        
        rsi_14_1d = round(self.rsi_calculator.calculate(close1D), 0)  # RSI保留0位小数
        atr_1d = round(self.atr_calculator.calculate(df), 0)  # ATR保留0位小数
        
        bollinger_upper_1d, bollinger_lower_1d, bollinger_position_1d = self.bollinger_calculator.calculate(close1D)
        bollinger_upper_1d = round((bollinger_upper_1d - self.close_mean) / self.close_std, 3)  # 价格标准化保留3位小数
        bollinger_lower_1d = round((bollinger_lower_1d - self.close_mean) / self.close_std, 3)  # 价格标准化保留3位小数
        
        pinbar_features = self.pinbar_calculator.calculate(
            high_prices=df['high'],
            low_prices=df['low'],
            open_prices=df['open'],
            close_prices=df['close']
        )
        
        return {
            "rsi_14_1d": rsi_14_1d,
            "atr_1d": atr_1d,
            "bollinger_upper_1d": bollinger_upper_1d,
            "bollinger_lower_1d": bollinger_lower_1d,
            "bollinger_position_1d": round(bollinger_position_1d, 2),  # 位置标准化保留2位小数
            "upper_shadow_ratio_1d": round(pinbar_features['upper_shadow_ratio'], 2),
            "lower_shadow_ratio_1d": round(pinbar_features['lower_shadow_ratio'], 2),
            "shadow_imbalance_1d": round(pinbar_features['shadow_imbalance'], 2),
            "body_ratio_1d": round(pinbar_features['body_ratio'], 2),
        }
    