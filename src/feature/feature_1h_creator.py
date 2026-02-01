
import pandas as pd

from typing import List, Dict, Any, Tuple

from utils.rsi_calculator import RSI_CALCULATOR
from utils.macd_calculator import MACD_CALCULATOR
from utils.time_encoder import TIMESTAMP_ENCODER
from utils.impulse_calculator import IMPULSE_CALCULATOR
from utils.calculator_interface import BaseTechnicalCalculator

class Feature1HCreator(BaseTechnicalCalculator):

    """
    FeatureCreator 最小可用版本 只包含一些基本的参数
    """
    def __init__(self, close_mean: float, close_std: float, vol_mean: float, vol_std: float):
        self.rsi_calculator = RSI_CALCULATOR
        self.macd_calculator = MACD_CALCULATOR
        self.ts_encoder = TIMESTAMP_ENCODER
        self.vi_calculator = IMPULSE_CALCULATOR
        self.close_mean = close_mean
        self.close_std = close_std
        self.vol_mean = vol_mean
        self.vol_std = vol_std
        
        
    def calculate(self, candles1h: List[Dict[str, Any]]) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """
            处理一小时的特征参数
        Args:
            candles (List[Dict[str, Any]]): 48条数据（因为macd慢线需要48的时间窗口）
            Returns:
            Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
            "close_1h_normalized": Number,    // 价格标准化
            "volume_1h_normalized": Number,   // 成交量标准化
            "rsi_14_1h": Number,              // 标准短期动量指标
            "macd_line_1h": Number,           // MACD快线
            "macd_signal_1h": Number,         // MACD信号线
            
        """
        close1h = pd.Series(item['close'] for item in candles1h)
        volume1h = pd.Series(item['volume'] for item in candles1h)
        
        close_1h_normalized = (close1h.iloc[-1] - self.close_mean) / self.close_std
        volume_1h_normalized = (volume1h.iloc[-1] - self.vol_mean) / self.vol_std
        
        rsi_14_1h = self.rsi_calculator.calculate(close1h)
        macd_line_1h, macd_signal_1h, _ = self.macd_calculator.calculate(close1h)
        return close_1h_normalized, volume_1h_normalized, rsi_14_1h, macd_line_1h,macd_signal_1h
    