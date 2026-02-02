from feature.feature_1h_creator import Feature1HCreator
from feature.feature_15m_creator import Feature15mCreator
from feature.feature_4h_creator import Feature4HCreator
from collect.candlestick_handler import candlestick_handler
from collect.normalization_handler import normalization_handler
from collect.feature_handler import feature_handler

class FeatureMerge:
    
    def process(self, inst_id: str, before: int = None) -> bool:
        """
        合并1小时、15分钟和4小时的特征参数
        """
        candles1H = candlestick_handler.get_candlestick_data(inst_id = inst_id, bar = '1H', limit = 48, before = before)
        candles15m = candlestick_handler.get_candlestick_data(inst_id = inst_id, bar = '15m', limit = 48, before = before)
        candles4H = candlestick_handler.get_candlestick_data(inst_id = inst_id, bar = '4H', limit = 48, before = before)
        
        if candles1H is None or candles15m is None or candles4H is None:
            return False
        
        is_close_saved = normalization_handler.get_normalization_params(inst_id = inst_id, bar = '1H', column = 'close')
        is_volume_saved = normalization_handler.get_normalization_params(inst_id = inst_id, bar = '1H', column = 'volume')
        
        if not is_close_saved or not is_volume_saved:
            return False
        
        feature1h = Feature1HCreator(close_mean = is_close_saved['mean'], 
                                    close_std = is_close_saved['std'], 
                                    vol_mean = is_volume_saved['mean'], 
                                    vol_std = is_volume_saved['std']);
        feature15m = Feature15mCreator();
        feature4h = Feature4HCreator();
        
        feature1h_result = feature1h.calculate(candles1H)
        feature15m_result = feature15m.calculate(candles15m)
        feature4h_result = feature4h.calculate(candles4H)
        
        # 合并特征到一个字典中
        features = {
            # 1小时基础特征
            "close_1h_normalized": feature1h_result.get("close_1h_normalized"),
            "volume_1h_normalized": feature1h_result.get("volume_1h_normalized"),
            "rsi_14_1h": feature1h_result.get("rsi_14_1h"),
            "macd_line_1h": feature1h_result.get("macd_line_1h"),
            "macd_signal_1h": feature1h_result.get("macd_signal_1h"),
            
            # 时间编码特征
            "hour_cos": feature1h_result.get("hour_cos"),
            "hour_sin": feature1h_result.get("hour_sin"),
            "day_of_week": feature1h_result.get("day_of_week"),
            
            # 15分钟高频特征
            "rsi_14_15m": feature15m_result.get("rsi_14_15m"),
            "volume_impulse_15m": feature15m_result.get("volume_impulse_15m"),
            "macd_line_15m": feature15m_result.get("macd_line_15m"),
            "macd_signal_15m": feature15m_result.get("macd_signal_15m"),
            
            # 4小时中期特征
            "rsi_14_4h": feature4h_result.get("rsi_14_4h"),
            "trend_continuation_4h": feature4h_result.get("trend_continuation_4h"),
            "macd_line_4h": feature4h_result.get("macd_line_4h"),
            "macd_signal_4h": feature4h_result.get("macd_signal_4h"),
            
            # 基本信息
            "inst_id": inst_id,
            "bar": "1H"
        }
        
        # 获取 candles1H 的最后一条数据的 timestamp
        if candles1H:
            features["timestamp"] = candles1H[-1].get("timestamp")
        else:
            return False
        
        # 保存特征数据
        try:
            success = feature_handler.save_features([features])
            if success:
                print(f"成功保存特征数据，timestamp: {features['timestamp']}")
            return success
        except Exception as e:
            print(f"保存特征数据失败: {e}")
            return False