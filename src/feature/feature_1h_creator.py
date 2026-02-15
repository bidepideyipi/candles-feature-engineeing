
import pandas as pd
import numpy as np
from typing import List, Dict, Any

from utils.rsi_calculator import RSI_CALCULATOR
from utils.macd_calculator import MACD_CALCULATOR
from utils.pinbar_calculator import PINBAR_CALCULATOR
from utils.calculator_interface import BaseTechnicalCalculator

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
        
        
    def calculate(self, candles1h: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
            处理一小时的特征参数
        Args:
            candles (List[Dict[str, Any]]): 48条数据（因为macd慢线需要48的时间窗口）
            Returns:
            Dict[str, Any]:
            "close_1h_normalized": Number,    // 价格标准化
            "volume_1h_normalized": Number,   // 成交量标准化
            "rsi_14_1h": Number,              // 标准短期动量指标
            "macd_line_1h": Number,           // MACD快线
            "macd_signal_1h": Number,         // MACD信号线
            
            时间编码特征
            "hour_cos": Number,               // 小时余弦编码
            "hour_sin": Number,               // 小时正弦编码
            "day_of_week": Number,            // 星期几
            
        """
        close1h = pd.Series(item['close'] for item in candles1h)
        volume1h = pd.Series(item['volume'] for item in candles1h)
        
        close_1h_normalized = round((close1h.iloc[-1] - self.close_mean) / self.close_std, 3)  # 价格标准化保留3位小数
        volume_1h_normalized = round((volume1h.iloc[-1] - self.vol_mean) / self.vol_std, 3)  # 成交量标准化保留3位小数
        
        rsi_14_1h = round(self.rsi_calculator.calculate(close1h), 0)  # RSI保留0位小数
        macd_line_1h, macd_signal_1h, macd_histogram_1h = self.macd_calculator.calculate(close1h)
        macd_line_1h = round(macd_line_1h, 0)  # MACD保留0位小数
        macd_signal_1h = round(macd_signal_1h, 0)  # MACD信号线保留0位小数
        macd_histogram_1h = round(macd_histogram_1h, 3)  # MACD直方图保留3位小数    
        
        # 直接在当前方法中实现时间编码转换
        # 获取最后一个记录的小时和星期几
        last_record = candles1h[-1]
        record_hour = last_record['record_hour']
        # merge的时候是从数据库取的，但从okex取的时候就不一样
        day_of_week = last_record['day_of_week']
        # 转换为弧度 (24小时 = 2π 弧度)
        hour_rad = record_hour * (2 * np.pi / 24)
        # 计算周期性特征
        hour_cos = round(np.cos(hour_rad), 4)
        hour_sin = round(np.sin(hour_rad), 4)
        
        # 计算 Pinbar 特征
        pinbar_features = self.pinbar_calculator.calculate(
            pd.Series(item['high'] for item in candles1h),
            pd.Series(item['low'] for item in candles1h),
            pd.Series(item['open'] for item in candles1h),
            pd.Series(item['close'] for item in candles1h)
        )
        
        return {
            "close_1h_normalized": close_1h_normalized,
            "volume_1h_normalized": volume_1h_normalized,
            "rsi_14_1h": rsi_14_1h,
            "macd_line_1h": macd_line_1h,
            "macd_signal_1h": macd_signal_1h,
            "macd_histogram_1h": macd_histogram_1h,
            "hour_cos": hour_cos,
            "hour_sin": hour_sin,
            "day_of_week": day_of_week,
            "upper_shadow_ratio_1h": round(pinbar_features['upper_shadow_ratio'], 2),
            "lower_shadow_ratio_1h": round(pinbar_features['lower_shadow_ratio'], 2),
            "shadow_imbalance_1h": round(pinbar_features['shadow_imbalance'], 2),
            "body_ratio_1h": round(pinbar_features['body_ratio'], 2),
          }
    