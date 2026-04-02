import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from feature.feature_1h_creator import Feature1HCreator
from feature.feature_15m_creator import Feature15mCreator
from feature.feature_4h_creator import Feature4HCreator
from feature.feature_1d_creator import Feature1DCreator
from feature.feature_types import Feature
from collect.candlestick_handler import candlestick_handler
from collect.normalization_handler import normalization_handler
from collect.feature_handler import feature_handler
from collect.okex_fetcher import okex_fetcher
from collect.async_candlestick_handler import async_candlestick_handler

log = logging.getLogger(__name__)

class FeatureMerge:
    
    def __init__(self, batch_size: int = 1000):
        self.inst_id = "ETH-USDT-SWAP"
        self.batch_size = batch_size
        self._batch_cache: List[Feature] = []
    
    def loop(self, before: int = None, limit: int = 5000) -> bool:
        """
        循环合并特征
        """
        last_timestamp = before
        n = 0
        try:
            while last_timestamp is not None and n < limit:
                try:
                    result = self._process_and_cache(before=last_timestamp)
                    if result is not None:
                        last_timestamp = result
                        n += 1
                    else:
                        break
                except Exception as e:
                    log.error(f"处理特征时发生错误: {e}", exc_info=True)
                    break
        finally:
            if self._batch_cache:
                self._flush_batch()
        
        return True

    async def process_async(self, before: int = None) -> int:
        """
        合并1小时、15分钟和4小时的特征参数（异步版本）
        """
        results = await asyncio.gather(
            async_candlestick_handler.get_candlestick_data(inst_id=self.inst_id, bar='1H', limit=48, before=before),
            async_candlestick_handler.get_candlestick_data(inst_id=self.inst_id, bar='15m', limit=48, before=before),
            async_candlestick_handler.get_candlestick_data(inst_id=self.inst_id, bar='4H', limit=48, before=before),
            async_candlestick_handler.get_candlestick_data(inst_id=self.inst_id, bar='1D', limit=48, before=before),
            return_exceptions=True
        )
        
        candles1H = results[0][::-1] if not isinstance(results[0], Exception) else []
        candles15m = results[1][::-1] if not isinstance(results[1], Exception) else []
        candles4H = results[2][::-1] if not isinstance(results[2], Exception) else []
        candles1D = results[3][::-1] if not isinstance(results[3], Exception) else []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                bars = ['1H', '15m', '4H', '1D']
                log.error(f"Failed to get {bars[i]} candlestick data: {result}")
        
        features = self._common_process(candles1H=candles1H,candles15m=candles15m,candles4H=candles4H,candles1D=candles1D)
        
        if not features:
            return None
        
        try:
            success = feature_handler.save_features([features])
            if success:
                print(f"成功保存特征数据，timestamp: {features.timestamp}")
            
            return features.timestamp
        except Exception as e:
            print(f"保存特征数据失败: {e}")
            return None
    
    def process(self, before: int = None) -> int:
        """
        合并1小时、15分钟和4小时的特征参数（同步版本）
        始终使用同步 handler，避免与现有事件循环冲突
        """
        candles1H = candlestick_handler.get_candlestick_data(inst_id=self.inst_id, bar='1H', limit=48, before=before)[::-1]
        candles15m = candlestick_handler.get_candlestick_data(inst_id=self.inst_id, bar='15m', limit=48, before=before)[::-1]
        candles4H = candlestick_handler.get_candlestick_data(inst_id=self.inst_id, bar='4H', limit=48, before=before)[::-1]
        candles1D = candlestick_handler.get_candlestick_data(inst_id=self.inst_id, bar='1D', limit=48, before=before)[::-1]
        
        if not candles1H or not candles15m or not candles4H or not candles1D:
            log.warning(f"获取数据失败或为空, 1H: {len(candles1H) if candles1H else 0}, 15m: {len(candles15m) if candles15m else 0}, 4H: {len(candles4H) if candles4H else 0}, 1D: {len(candles1D) if candles1D else 0}")
            return None
        
        features = self._common_process(candles1H=candles1H,candles15m=candles15m,candles4H=candles4H,candles1D=candles1D)
        
        if not features:
            return None
        
        try:
            success = feature_handler.save_features([features])
            if success:
                print(f"成功保存特征数据，timestamp: {features.timestamp}")
            return features.timestamp
        except Exception as e:
            print(f"保存特征数据失败: {e}")
            return None      
    
    def quick_process_eth(self) -> Optional[Feature]:
        """
        快速处理 ETH-USDT-SWAP 的实时数据进行特征提取
        使用实时 API 获取最新 K 线数据并计算特征
        """
        realtime_candles = okex_fetcher.fetch_realtime_candles(inst_id=self.inst_id)
        
        if not realtime_candles:
            log.error("获取实时 K 线数据失败")
            return None
        
        candles1H = self._convert_realtime_candles(realtime_candles.get("1H", []), bar="1H")[::-1]
        candles15m = self._convert_realtime_candles(realtime_candles.get("15m", []), bar="15m")[::-1]
        candles4H = self._convert_realtime_candles(realtime_candles.get("4H", []), bar="4H")[::-1]
        candles1D = self._convert_realtime_candles(realtime_candles.get("1D", []), bar="1D")[::-1]
        
        features = self._common_process(candles1H=candles1H, candles15m=candles15m, candles4H=candles4H, candles1D=candles1D)
        
        if features:
            log.info(f"成功提取 ETH 实时特征，timestamp: {features.timestamp}")
        
        return features
    
    def quick_process_eth_from_mongodb(self) -> Optional[Feature]:
        """
        快速处理 ETH-USDT-SWAP 的数据进行特征提取（无网络版）
        从 MongoDB candlestick 集合获取最近的数据并计算特征
        """
        try:
            candles1H = candlestick_handler.get_candlestick_data(
                inst_id=self.inst_id, 
                bar='1H', 
                limit=48
            )[::-1]
            
            candles15m = candlestick_handler.get_candlestick_data(
                inst_id=self.inst_id, 
                bar='15m', 
                limit=48
            )[::-1]
            
            candles4H = candlestick_handler.get_candlestick_data(
                inst_id=self.inst_id, 
                bar='4H', 
                limit=48
            )[::-1]
            
            candles1D = candlestick_handler.get_candlestick_data(
                inst_id=self.inst_id, 
                bar='1D', 
                limit=48
            )[::-1]
            
            if not candles1H or not candles15m or not candles4H or not candles1D:
                log.error("MongoDB 中数据不足")
                return None
            
            features = self._common_process(
                candles1H=candles1H, 
                candles15m=candles15m, 
                candles4H=candles4H, 
                candles1D=candles1D
            )
            
            if features:
                log.info(f"成功从 MongoDB 提取 ETH 特征，timestamp: {features.timestamp}")
            
            return features
            
        except Exception as e:
            log.error(f"从 MongoDB 提取特征失败: {e}")
            return None
    
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
                    "day_of_week": dt.weekday()
                }
                converted.append(converted_candle)
            except (IndexError, ValueError) as e:
                log.warning(f"转换 K 线数据失败: {e}, candle: {candle}")
                continue
        
        return converted
        
    def _common_process(self, candles1H: List[Dict[str, Any]], candles15m: List[Dict[str, Any]], candles4H: List[Dict[str, Any]], candles1D: List[Dict[str, Any]]) -> Optional[Feature]:
        if candles1H is None or candles15m is None or candles4H is None or candles1D is None:
            log.warning(f"获取数据失败, 1H: {candles1H}, 15m: {candles15m}, 4H: {candles4H}, 1D: {candles1D}")
            return None
        if len(candles1H) != 48 or len(candles15m) != 48 or len(candles4H) != 48 or len(candles1D) != 48:
            log.warning(f"数据长度不一致, 1H: {len(candles1H)}, 15m: {len(candles15m)}, 4H: {len(candles4H)}, 1D: {len(candles1D)}")
            return None
        
        try:
            last_1h = candles1H[-1]
            last_15m = candles15m[-1]
            last_4h = candles4H[-1]
            last_1d = candles1D[-1]
            
            if last_1h.get('record_dt') != last_1d.get('record_dt'):
                log.warning(f"1H和1D的日期不一致, 1H: {last_1h.get('record_dt')}, 1D: {last_1d.get('record_dt')}, last_1h: {last_1h.get('timestamp')}")
                return None
            
            if last_1h.get('record_dt') != last_15m.get('record_dt'):
                log.warning(f"1H和15m的日期不一致, 1H: {last_1h.get('record_dt')}, 15m: {last_15m.get('record_dt')}, last_1h: {last_1h.get('timestamp')}")
                return None
            if last_1h.get('record_hour') != last_15m.get('record_hour'):
                log.warning(f"1H和15m的小时不一致, 1H: {last_1h.get('record_hour')}, 15m: {last_15m.get('record_hour')}, last_1h: {last_1h.get('timestamp')}")
                return None
            
            if last_1h.get('record_dt') != last_4h.get('record_dt'):
                log.warning(f"1H和4H的日期不一致, 1H: {last_1h.get('record_dt')}, 4H: {last_4h.get('record_dt')}, last_1h: {last_1h.get('timestamp')}")
                return None
            
            hour_diff = last_1h.get('record_hour') - last_4h.get('record_hour')
            if hour_diff < 0 or hour_diff > 3:
                log.warning(f"1H和4H的小时差不在有效范围内, 差值: {hour_diff}, last_1h: {last_1h.get('timestamp')}")
                return None
            
            for i in range(47):
                if candles1H[i+1].get('timestamp') != candles1H[i].get('timestamp') + 60 * 60 * 1000:
                    log.warning(f"1H数据不连续, 索引: {i}, 时间差: {candles1H[i+1].get('timestamp') - candles1H[i].get('timestamp')}")
                    return None
            for i in range(47):
                if candles15m[i+1].get('timestamp') != candles15m[i].get('timestamp') + 15 * 60 * 1000:
                    log.warning(f"15m数据不连续, 索引: {i}, 时间差: {candles15m[i+1].get('timestamp') - candles15m[i].get('timestamp')}")
                    return None
            for i in range(47):
                if candles4H[i+1].get('timestamp') != candles4H[i].get('timestamp') + 4 * 60 * 60 * 1000:
                    log.warning(f"4H数据不连续, 索引: {i}, 时间差: {candles4H[i+1].get('timestamp') - candles4H[i].get('timestamp')}")
                    return None
            for i in range(47):
                if candles1D[i+1].get('timestamp') != candles1D[i].get('timestamp') + 24 * 60 * 60 * 1000:
                    log.warning(f"1D数据不连续, 索引: {i}, 时间差: {candles1D[i+1].get('timestamp') - candles1D[i].get('timestamp')}")
                    return None
                
        except (IndexError, KeyError) as e:
            log.warning(f"时间字段校验失败: {e}")
            return None
        
        is_close_saved = normalization_handler.get_normalization_params(inst_id=self.inst_id, bar='1H', column='close')
        is_volume_saved = normalization_handler.get_normalization_params(inst_id=self.inst_id, bar='1H', column='volume')
        
        if not is_close_saved or not is_volume_saved:
            return None
        
        feature1h = Feature1HCreator(close_mean=is_close_saved['mean'], 
                                    close_std=is_close_saved['std'], 
                                    vol_mean=is_volume_saved['mean'], 
                                    vol_std=is_volume_saved['std'])
        feature15m = Feature15mCreator()
        feature4h = Feature4HCreator(close_mean=is_close_saved['mean'], 
                                    close_std=is_close_saved['std'])
        feature1D = Feature1DCreator(close_mean=is_close_saved['mean'], 
                                    close_std=is_close_saved['std'])
        
        feature1h_result = feature1h.calculate(candles1H)
        feature15m_result = feature15m.calculate(candles15m)
        feature4h_result = feature4h.calculate(candles4H)
        feature1D_result = feature1D.calculate(candles1D)
        
        feature = Feature(
            timestamp=last_1h.get('timestamp'),
            inst_id=self.inst_id,
            bar="1H",
            close_1h_normalized=feature1h_result.close_1h_normalized,
            volume_1h_normalized=feature1h_result.volume_1h_normalized,
            rsi_14_1h=feature1h_result.rsi_14_1h,
            macd_line_1h=feature1h_result.macd_line_1h,
            macd_signal_1h=feature1h_result.macd_signal_1h,
            macd_histogram_1h=feature1h_result.macd_histogram_1h,
            price=feature1h_result.price,
            hour_cos=feature1h_result.hour_cos,
            hour_sin=feature1h_result.hour_sin,
            day_of_week=feature1h_result.day_of_week,
            upper_shadow_ratio_1h=feature1h_result.upper_shadow_ratio_1h,
            lower_shadow_ratio_1h=feature1h_result.lower_shadow_ratio_1h,
            shadow_imbalance_1h=feature1h_result.shadow_imbalance_1h,
            body_ratio_1h=feature1h_result.body_ratio_1h,
            atr_1h=feature1h_result.atr_1h,
            adx_1h=feature1h_result.adx_1h,
            plus_di_1h=feature1h_result.plus_di_1h,
            minus_di_1h=feature1h_result.minus_di_1h,
            ema_12_1h=feature1h_result.ema_12_1h,
            ema_26_1h=feature1h_result.ema_26_1h,
            ema_48_1h=feature1h_result.ema_48_1h,
            ema_cross_1h_12_26=feature1h_result.ema_cross_1h_12_26,
            ema_cross_1h_26_48=feature1h_result.ema_cross_1h_26_48,
            rsi_14_15m=feature15m_result.rsi_14_15m,
            volume_impulse_15m=feature15m_result.volume_impulse_15m,
            macd_line_15m=feature15m_result.macd_line_15m,
            macd_signal_15m=feature15m_result.macd_signal_15m,
            macd_histogram_15m=feature15m_result.macd_histogram_15m,
            atr_15m=feature15m_result.atr_15m,
            stoch_k_15m=feature15m_result.stoch_k_15m,
            stoch_d_15m=feature15m_result.stoch_d_15m,
            rsi_14_4h=feature4h_result.rsi_14_4h,
            trend_continuation_4h=feature4h_result.trend_continuation_4h,
            macd_line_4h=feature4h_result.macd_line_4h,
            macd_signal_4h=feature4h_result.macd_signal_4h,
            macd_histogram_4h=feature4h_result.macd_histogram_4h,
            atr_4h=feature4h_result.atr_4h,
            adx_4h=feature4h_result.adx_4h,
            plus_di_4h=feature4h_result.plus_di_4h,
            minus_di_4h=feature4h_result.minus_di_4h,
            ema_12_4h=feature4h_result.ema_12_4h,
            ema_26_4h=feature4h_result.ema_26_4h,
            ema_48_4h=feature4h_result.ema_48_4h,
            ema_cross_4h_12_26=feature4h_result.ema_cross_4h_12_26,
            ema_cross_4h_26_48=feature4h_result.ema_cross_4h_26_48,
            upper_shadow_ratio_4h=feature4h_result.upper_shadow_ratio_4h,
            lower_shadow_ratio_4h=feature4h_result.lower_shadow_ratio_4h,
            shadow_imbalance_4h=feature4h_result.shadow_imbalance_4h,
            body_ratio_4h=feature4h_result.body_ratio_4h,
            rsi_14_1d=feature1D_result.rsi_14_1d,
            atr_1d=feature1D_result.atr_1d,
            bollinger_upper_1d=feature1D_result.bollinger_upper_1d,
            bollinger_lower_1d=feature1D_result.bollinger_lower_1d,
            bollinger_position_1d=feature1D_result.bollinger_position_1d,
            upper_shadow_ratio_1d=feature1D_result.upper_shadow_ratio_1d,
            lower_shadow_ratio_1d=feature1D_result.lower_shadow_ratio_1d,
            shadow_imbalance_1d=feature1D_result.shadow_imbalance_1d,
            body_ratio_1d=feature1D_result.body_ratio_1d,
            macd_line_1d=feature1D_result.macd_line_1d,
            macd_signal_1d=feature1D_result.macd_signal_1d,
        )
        
        return feature
    
    def _process_and_cache(self, before: int = None) -> Optional[int]:
        """
        处理单条数据并添加到缓存，当缓存达到 batch_size 时批量保存
        """
        candles1H = candlestick_handler.get_candlestick_data(inst_id=self.inst_id, bar='1H', limit=48, before=before)[::-1]
        candles15m = candlestick_handler.get_candlestick_data(inst_id=self.inst_id, bar='15m', limit=48, before=before)[::-1]
        candles4H = candlestick_handler.get_candlestick_data(inst_id=self.inst_id, bar='4H', limit=48, before=before)[::-1]
        candles1D = candlestick_handler.get_candlestick_data(inst_id=self.inst_id, bar='1D', limit=48, before=before)[::-1]
        
        if not candles1H or not candles15m or not candles4H or not candles1D:
            log.warning(f"获取数据失败或为空, 1H: {len(candles1H) if candles1H else 0}, 15m: {len(candles15m) if candles15m else 0}, 4H: {len(candles4H) if candles4H else 0}, 1D: {len(candles1D) if candles1D else 0}")
            return None
        
        features = self._common_process(candles1H=candles1H, candles15m=candles15m, candles4H=candles4H, candles1D=candles1D)
        
        if not features:
            return None
        
        self._batch_cache.append(features)
        
        if len(self._batch_cache) >= self.batch_size:
            self._flush_batch()
        
        return features.timestamp
    
    def _flush_batch(self) -> bool:
        """
        批量保存缓存中的特征数据
        """
        if not self._batch_cache:
            return True
        
        try:
            success = feature_handler.save_features(self._batch_cache)
            if success:
                log.info(f"成功批量保存 {len(self._batch_cache)} 条特征数据")
                self._batch_cache = []
                return True
            else:
                log.error(f"批量保存特征数据失败")
                return False
        except Exception as e:
            log.error(f"批量保存特征数据失败: {e}")
            return False
          