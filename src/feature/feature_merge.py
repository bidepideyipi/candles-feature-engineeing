import logging
from datetime import datetime
from typing import Dict, Any, List
from feature.feature_1h_creator import Feature1HCreator
from feature.feature_15m_creator import Feature15mCreator
from feature.feature_4h_creator import Feature4HCreator
from feature.feature_1d_creator import Feature1DCreator
from collect.candlestick_handler import candlestick_handler
from collect.normalization_handler import normalization_handler
from collect.feature_handler import feature_handler
from collect.okex_fetcher import okex_fetcher

# Create logger
log = logging.getLogger(__name__)

class FeatureMerge:
    
    def __init__(self):
        self.inst_id = "ETH-USDT-SWAP"
    
    def loop(self, before: int = None, limit: int = 5000) -> bool:
        """
        循环合并特征
        """
        last_timestamp = before
        n = 0
        while last_timestamp is not None and n < limit:
            last_timestamp = self.process(before = last_timestamp)
            n += 1
        return True

    def process(self, before: int = None) -> int:
        """
        合并1小时、15分钟和4小时的特征参数
        """
        candles1H = candlestick_handler.get_candlestick_data(inst_id = self.inst_id, bar = '1H', limit = 48, before = before)[::-1]
        candles15m = candlestick_handler.get_candlestick_data(inst_id = self.inst_id, bar = '15m', limit = 48, before = before)[::-1]
        candles4H = candlestick_handler.get_candlestick_data(inst_id = self.inst_id, bar = '4H', limit = 48, before = before)[::-1]
        candles1D = candlestick_handler.get_candlestick_data(inst_id = self.inst_id, bar = '1D', limit = 48, before = before)[::-1]
        features = self._common_process(candles1H=candles1H,candles15m=candles15m,candles4H=candles4H,candles1D=candles1D)
        
        # 获取 candles1H 的最后一条数据的 timestamp
        if candles1H:
            features["timestamp"] = candles1H[-1].get("timestamp")
        else:
            return None
        
        # 保存特征数据
        try:
            success = feature_handler.save_features([features])
            if success:
                print(f"成功保存特征数据，timestamp: {features['timestamp']}")
            
            return features["timestamp"]
        except Exception as e:
            print(f"保存特征数据失败: {e}")
            return None      
    
    def quick_process_eth(self) -> Dict[str, Any]:
        """
        快速处理 ETH-USDT-SWAP 的实时数据进行特征提取
        使用实时 API 获取最新 K 线数据并计算特征
        """
        realtime_candles = okex_fetcher.fetch_realtime_candles(inst_id=self.inst_id)
        
        if not realtime_candles:
            log.error("获取实时 K 线数据失败")
            return None
        
        # 转换实时数据格式为 _common_process 支持的格式
        candles1H = self._convert_realtime_candles(realtime_candles.get("1H", []), bar="1H")[::-1]
        candles15m = self._convert_realtime_candles(realtime_candles.get("15m", []), bar="15m")[::-1]
        candles4H = self._convert_realtime_candles(realtime_candles.get("4H", []), bar="4H")[::-1]
        candles1D = self._convert_realtime_candles(realtime_candles.get("1D", []), bar="1D")[::-1]
        
        # 调用通用处理方法获取特征
        features = self._common_process(candles1H=candles1H, candles15m=candles15m, candles4H=candles4H, candles1D=candles1D)
        
        if features:
            log.info(f"成功提取 ETH 实时特征，timestamp: {features.get('timestamp')}")
        
        return features
    
    def _convert_realtime_candles(self, candles: List[List[str]], bar: str) -> List[Dict[str, Any]]:
        """
        将实时 API 返回的 K 线数据转换为 _common_process 支持的格式
        
        Args:
            candles: 实时 API 返回的 K 线数据，格式为 [[timestamp, open, high, low, close, volume, ...], ...]
            bar: 时间周期 (15m, 1H, 4H, 1D)
        
        Returns:
            转换后的 K 线数据列表
        """
        if not candles:
            return []
        
        converted = []
        for candle in candles:
            try:
                timestamp = int(candle[0])
                dt = datetime.fromtimestamp(timestamp / 1000)
                
                converted_candle = {
                    "timestamp": timestamp,
                    "open": float(candle[1]),
                    "high": float(candle[2]),
                    "low": float(candle[3]),
                    "close": float(candle[4]),
                    "volume": float(candle[5]),
                    "inst_id": self.inst_id,
                    "bar": bar,
                    "record_dt": dt.date(),
                    "record_hour": dt.hour,
                    "record_day_of_week": dt.weekday()
                }
                converted.append(converted_candle)
            except (IndexError, ValueError) as e:
                log.warning(f"转换 K 线数据失败: {e}, candle: {candle}")
                continue
        
        return converted
        
    def _common_process(self, candles1H :List[Dict[str, Any]], candles15m :List[Dict[str, Any]], candles4H: List[Dict[str, Any]], candles1D :List[Dict[str, Any]]) -> Dict[str, Any]:
        if candles1H is None or candles15m is None or candles4H is None or candles1D is None:
            log.warning(f"获取数据失败, 1H: {candles1H}, 15m: {candles15m}, 4H: {candles4H}, 1D: {candles1D}")
            return None
        if len(candles1H) != 48 or len(candles15m) != 48 or len(candles4H) != 48 or len(candles1D) != 48:
            log.warning(f"数据长度不一致, 1H: {len(candles1H)}, 15m: {len(candles15m)}, 4H: {len(candles4H)}, 1D: {len(candles1D)}")
            return None
        
        # 数据时间一致性校验
        try:
            # 获取各时间周期的最后一条数据
            last_1h = candles1H[-1]
            last_15m = candles15m[-1]
            last_4h = candles4H[-1]
            last_1d = candles1D[-1]
            
            # 校验1H和1D的日期一致性
            if last_1h.get('record_dt') != last_1d.get('record_dt'):
                log.warning(f"1H和1D的日期不一致, 1H: {last_1h.get('record_dt')}, 1D: {last_1d.get('record_dt')}, last_1h: {last_1h.get('timestamp')}")
                return None
            
            # 校验1H和15m的时间一致性
            if last_1h.get('record_dt') != last_15m.get('record_dt'):
                log.warning(f"1H和15m的日期不一致, 1H: {last_1h.get('record_dt')}, 15m: {last_15m.get('record_dt')}, last_1h: {last_1h.get('timestamp')}")
                return None
            if last_1h.get('record_hour') != last_15m.get('record_hour'):
                log.warning(f"1H和15m的小时不一致, 1H: {last_1h.get('record_hour')}, 15m: {last_15m.get('record_hour')}, last_1h: {last_1h.get('timestamp')}")
                return None
            
            # 校验1H和4H的时间一致性
            if last_1h.get('record_dt') != last_4h.get('record_dt'):
                log.warning(f"1H和4H的日期不一致, 1H: {last_1h.get('record_dt')}, 4H: {last_4h.get('record_dt')}, last_1h: {last_1h.get('timestamp')}")
                return None
            
            # 校验1H和4H的小时差
            hour_diff = last_1h.get('record_hour') - last_4h.get('record_hour')
            if hour_diff < 0 or hour_diff > 3:
                log.warning(f"1H和4H的小时差不在有效范围内, 差值: {hour_diff}, last_1h: {last_1h.get('timestamp')}")
                return None
            
            # 检查1H的数据是不是连续的
            for i in range(47):
                if candles1H[i+1].get('timestamp') != candles1H[i].get('timestamp') + 60 * 60 * 1000:
                    log.warning(f"1H数据不连续, 索引: {i}, 时间差: {candles1H[i+1].get('timestamp') - candles1H[i].get('timestamp')}")
                    return None
            # 检查15m的数据是不是连续的
            for i in range(47):
                if candles15m[i+1].get('timestamp') != candles15m[i].get('timestamp') + 15 * 60 * 1000:
                    log.warning(f"15m数据不连续, 索引: {i}, 时间差: {candles15m[i+1].get('timestamp') - candles15m[i].get('timestamp')}")
                    return None
            # 检查4H的数据是不是连续的
            for i in range(47):
                if candles4H[i+1].get('timestamp') != candles4H[i].get('timestamp') + 4 * 60 * 60 * 1000:
                    log.warning(f"4H数据不连续, 索引: {i}, 时间差: {candles4H[i+1].get('timestamp') - candles4H[i].get('timestamp')}")
                    return None
            # 检查1D的数据是不是连续的
            for i in range(47):
                if candles1D[i+1].get('timestamp') != candles1D[i].get('timestamp') + 24 * 60 * 60 * 1000:
                    log.warning(f"1D数据不连续, 索引: {i}, 时间差: {candles1D[i+1].get('timestamp') - candles1D[i].get('timestamp')}")
                    return None
                
        except (IndexError, KeyError) as e:
            log.warning(f"时间字段校验失败: {e}")
            return None
        
        is_close_saved = normalization_handler.get_normalization_params(inst_id = self.inst_id, bar = '1H', column = 'close')
        is_volume_saved = normalization_handler.get_normalization_params(inst_id = self.inst_id, bar = '1H', column = 'volume')
        
        if not is_close_saved or not is_volume_saved:
            return None
        
        feature1h = Feature1HCreator(close_mean = is_close_saved['mean'], 
                                    close_std = is_close_saved['std'], 
                                    vol_mean = is_volume_saved['mean'], 
                                    vol_std = is_volume_saved['std']);
        feature15m = Feature15mCreator();
        feature4h = Feature4HCreator(close_mean = is_close_saved['mean'], 
                                    close_std = is_close_saved['std']);
        feature1D = Feature1DCreator(close_mean = is_close_saved['mean'], 
                                    close_std = is_close_saved['std']);
        
        feature1h_result = feature1h.calculate(candles1H)
        feature15m_result = feature15m.calculate(candles15m)
        feature4h_result = feature4h.calculate(candles4H)
        feature1D_result = feature1D.calculate(candles1D)
        
        # 合并特征到一个字典中
        features = {
            # 1小时基础特征
            "close_1h_normalized": feature1h_result.get("close_1h_normalized"),
            "volume_1h_normalized": feature1h_result.get("volume_1h_normalized"),
            "rsi_14_1h": feature1h_result.get("rsi_14_1h"),
            "macd_line_1h": feature1h_result.get("macd_line_1h"),
            "macd_signal_1h": feature1h_result.get("macd_signal_1h"),
            "macd_histogram_1h": feature1h_result.get("macd_histogram_1h"),
            
            # 时间编码特征
            "hour_cos": feature1h_result.get("hour_cos"),
            "hour_sin": feature1h_result.get("hour_sin"),
            "day_of_week": feature1h_result.get("day_of_week"),
            
            # 15分钟高频特征
            "rsi_14_15m": feature15m_result.get("rsi_14_15m"),
            "volume_impulse_15m": feature15m_result.get("volume_impulse_15m"),
            "macd_line_15m": feature15m_result.get("macd_line_15m"),
            "macd_signal_15m": feature15m_result.get("macd_signal_15m"),
            "macd_histogram_15m": feature15m_result.get("macd_histogram_15m"),
            "atr_15m": feature15m_result.get("atr_15m"),
            "stoch_k_15m": feature15m_result.get("stoch_k_15m"),
            "stoch_d_15m": feature15m_result.get("stoch_d_15m"),
            
            # 4小时中期特征
            "rsi_14_4h": feature4h_result.get("rsi_14_4h"),
            "trend_continuation_4h": feature4h_result.get("trend_continuation_4h"),
            "macd_line_4h": feature4h_result.get("macd_line_4h"),
            "macd_signal_4h": feature4h_result.get("macd_signal_4h"),
            "macd_histogram_4h" : feature4h_result.get("macd_histogram_4h"),
            "atr_4h": feature4h_result.get("atr_4h"),
            "adx_4h": feature4h_result.get("adx_4h"),
            "plus_di_4h": feature4h_result.get("plus_di_4h"),
            "minus_di_4h": feature4h_result.get("minus_di_4h"),
            "ema_12_4h": feature4h_result.get("ema_12_4h"),
            "ema_26_4h": feature4h_result.get("ema_26_4h"),
            "ema_48_4h": feature4h_result.get("ema_48_4h"),
            "ema_cross_4h_12_26": feature4h_result.get("ema_cross_4h_12_26"),
            "ema_cross_4h_26_48": feature4h_result.get("ema_cross_4h_26_48"),
            
            # 1天长期特征
            "rsi_14_1d": feature1D_result.get("rsi_14_1d"),
            "atr_1d": feature1D_result.get("atr_1d"),
            "bollinger_upper_1d": feature1D_result.get("bollinger_upper_1d"),
            "bollinger_lower_1d": feature1D_result.get("bollinger_lower_1d"),
            "bollinger_position_1d": feature1D_result.get("bollinger_position_1d"),
            
            # 基本信息
            "inst_id": self.inst_id,
            "bar": "1H"
        }
        
        return features
        
          