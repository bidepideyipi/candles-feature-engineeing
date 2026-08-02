import asyncio
import logging
from bisect import bisect_left
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from feature.feature_1h_creator import Feature1HCreator
from feature.feature_15m_creator import Feature15mCreator
from feature.feature_4h_creator import Feature4HCreator
from feature.feature_1d_creator import Feature1DCreator
from feature.feature_types import Feature
from collect.candlestick_handler import candlestick_handler
from collect.feature_handler import feature_handler
from collect.okex_fetcher import okex_fetcher
from collect.async_candlestick_handler import async_candlestick_handler
from config.settings import config
from utils.normalize_encoder import NORMALIZED

log = logging.getLogger(__name__)

MS_15M = 15 * 60 * 1000
MS_1H = 60 * 60 * 1000
MS_4H = 4 * MS_1H
MS_1D = 24 * MS_1H


class FeatureMerge:
    """
    Candlesticks → 1H feature rows.

    Bulk path (default in loop): one Mongo range load per bar, then in-memory
    sliding windows. Avoids ~4 DB round-trips per row (dominant cost at 20k).
    """

    def __init__(self, batch_size: int = 500):
        self.inst_id = "ETH-USDT-SWAP"
        self.batch_size = batch_size
        self._batch_cache: List[Feature] = []
        self.feature_window = config.FEATURE_CANDLE_WINDOW
        self.rolling_norm_window = config.ROLLING_NORM_WINDOW

    def _fetch_1h_for_norm(self, before: int = None) -> List[Dict[str, Any]]:
        """1H K 线：至少 feature_window 根用于指标，rolling_norm_window 根用于动态归一化。"""
        return self._fetch_candles("1H", self.rolling_norm_window, before)

    def _rolling_norm_params(self, candles1H: List[Dict[str, Any]]) -> Optional[Dict[str, float]]:
        if not candles1H or len(candles1H) < 2:
            return None
        norm_slice = candles1H[-self.rolling_norm_window:]
        close = [c['close'] for c in norm_slice]
        volume = [c['volume'] for c in norm_slice]
        try:
            _, close_mean, close_std = NORMALIZED.calculate_rolling(
                close, window=self.rolling_norm_window
            )
            _, vol_mean, vol_std = NORMALIZED.calculate_rolling(
                volume, window=self.rolling_norm_window
            )
            return {
                'mean': close_mean,
                'std': close_std,
                'vol_mean': vol_mean,
                'vol_std': vol_std,
            }
        except ValueError as e:
            log.warning("滚动归一化失败: %s", e)
            return None

    def _fetch_candles(self, bar: str, limit: int, before: Optional[int]) -> List[Dict[str, Any]]:
        """Fetch completed candles only and return ascending time order."""
        fetch_limit = limit + 2  # margin for a current unconfirmed candle
        if before is None:
            raw = candlestick_handler.get_candlestick_data(
                inst_id=self.inst_id, bar=bar, limit=fetch_limit, sort_desc=True
            )
        else:
            raw = candlestick_handler.get_candlestick_data(
                inst_id=self.inst_id, bar=bar, limit=fetch_limit, before=before
            )
        completed = [
            row for row in (raw or []) if int(row.get("confirm", 1)) == 1
        ]
        return list(reversed(completed[:limit]))

    def _resolve_initial_before(self, before: Optional[int]) -> Optional[int]:
        """从最新 1H K 线起点往历史回溯；无 K 线则返回 None。"""
        if before is not None:
            return before
        latest = candlestick_handler.get_latest_timestamp(self.inst_id, "1H")
        if latest is None:
            return None
        # 包含最新一根 1H
        return latest + MS_1H

    @staticmethod
    def _window_before(
        series: List[Dict[str, Any]],
        timestamps: List[int],
        before_excl: int,
        n: int,
    ) -> List[Dict[str, Any]]:
        """Last n candles with timestamp < before_excl (series ascending)."""
        if n <= 0 or not series:
            return []
        idx = bisect_left(timestamps, before_excl)
        start = max(0, idx - n)
        return series[start:idx]

    def _prefetch_ranges(
        self, cursor_before: int, limit: int
    ) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, List[int]], Optional[str]]:
        """
        One range query per bar covering lookback + `limit` 1H steps.
        """
        fw = self.feature_window
        lookback_ms = max(
            self.rolling_norm_window * MS_1H,
            fw * MS_15M,
            fw * MS_4H,
            fw * MS_1D,
        )
        # Extra day of margin for alignment edge cases
        start_ts = int(cursor_before) - int(limit) * MS_1H - lookback_ms - MS_1D
        end_ts = int(cursor_before)

        series: Dict[str, List[Dict[str, Any]]] = {}
        ts_index: Dict[str, List[int]] = {}
        for bar in ("1H", "15m", "4H", "1D"):
            rows = candlestick_handler.get_candlestick_range(
                self.inst_id, bar, start_ts, end_ts
            )
            if not rows:
                return {}, {}, f"prefetch empty for {bar} in [{start_ts}, {end_ts})"
            series[bar] = rows
            ts_index[bar] = [int(r["timestamp"]) for r in rows]
            log.info(
                "prefetch %s: %s candles [%s, %s)",
                bar,
                len(rows),
                rows[0]["timestamp"],
                end_ts,
            )
        return series, ts_index, None

    def loop(self, before: int = None, limit: int = 5000) -> Dict[str, Any]:
        """
        Merge features walking backward from latest (or `before`).

        Uses bulk prefetch + in-memory windows (not per-row Mongo fetches).
        """
        stats: Dict[str, Any] = {
            "processed": 0,
            "success": False,
            "before_start": before,
            "before_used": None,
            "last_error": None,
            "candle_counts": {},
            "mode": "bulk_prefetch",
        }

        cursor_before = self._resolve_initial_before(before)
        if cursor_before is None:
            stats["last_error"] = (
                "MongoDB 无 1H K 线，请先执行 /regime/pull-history 或 /regime/pipeline"
            )
            return stats

        stats["before_used"] = cursor_before
        stats["candle_counts"] = {
            "1H": candlestick_handler.count(self.inst_id, "1H"),
            "15m": candlestick_handler.count(self.inst_id, "15m"),
            "4H": candlestick_handler.count(self.inst_id, "4H"),
            "1D": candlestick_handler.count(self.inst_id, "1D"),
        }

        series, ts_index, pref_err = self._prefetch_ranges(cursor_before, limit)
        if pref_err:
            stats["last_error"] = pref_err
            return stats

        fw = self.feature_window
        rn = self.rolling_norm_window
        ts_1h = ts_index["1H"]
        # Select the latest `limit` targets, then calculate oldest → newest so
        # lag/delta features can use already-produced rows without future data.
        end_idx = bisect_left(ts_1h, cursor_before)
        start_idx = max(0, end_idx - limit)
        targets = ts_1h[start_idx:end_idx]
        history = (
            feature_handler.get_feature_history(
                self.inst_id, before=targets[0], bar="1H", limit=24
            )
            if targets
            else []
        )

        n = 0
        skipped_invalid = 0
        try:
            for target_ts in targets:
                if n >= limit:
                    break
                before_excl = int(target_ts) + MS_1H
                candles1H = self._window_before(
                    series["1H"], ts_index["1H"], before_excl, rn
                )
                candles15m = self._window_before(
                    series["15m"], ts_index["15m"], before_excl, fw
                )
                candles4H = self._window_before(
                    series["4H"], ts_index["4H"], before_excl, fw
                )
                candles1D = self._window_before(
                    series["1D"], ts_index["1D"], before_excl, fw
                )

                if (
                    len(candles1H) < fw
                    or len(candles15m) < fw
                    or len(candles4H) < fw
                    or len(candles1D) < fw
                ):
                    skipped_invalid += 1
                    log.warning(
                        "skip insufficient feature window ts=%s "
                        "1H=%s 15m=%s 4H=%s 1D=%s",
                        target_ts,
                        len(candles1H),
                        len(candles15m),
                        len(candles4H),
                        len(candles1D),
                    )
                    continue

                features = self._common_process(
                    candles1H=candles1H,
                    candles15m=candles15m,
                    candles4H=candles4H,
                    candles1D=candles1D,
                    history=history,
                )
                if not features:
                    skipped_invalid += 1
                    log.warning(
                        "bulk merge skipped invalid ts=%s "
                        "(alignment/continuity/normalization)",
                        target_ts,
                    )
                    continue

                self._batch_cache.append(features)
                history.append(features.to_dict())
                history = history[-24:]
                if len(self._batch_cache) >= self.batch_size:
                    self._flush_batch()
                n += 1
        except Exception as e:
            log.error("处理特征时发生错误: %s", e, exc_info=True)
            stats["last_error"] = str(e)
        finally:
            if self._batch_cache:
                self._flush_batch()

        stats["processed"] = n
        stats["skipped_invalid"] = skipped_invalid
        stats["success"] = n > 0
        if n == 0 and stats["last_error"] is None:
            stats["last_error"] = "首条 feature 校验未通过"
        return stats

    @staticmethod
    def _safe_delta(
        current: Dict[str, Any],
        history: List[Dict[str, Any]],
        field: str,
        lag: int,
    ) -> float:
        if len(history) < lag:
            return 0.0
        try:
            return round(
                float(current.get(field) or 0)
                - float(history[-lag].get(field) or 0),
                6,
            )
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _safe_return(
        current_price: float,
        history: List[Dict[str, Any]],
        lag: int,
    ) -> float:
        if len(history) < lag:
            return 0.0
        try:
            old = float(history[-lag].get("price") or 0)
            return round((float(current_price) / old) - 1.0, 6) if old else 0.0
        except (TypeError, ValueError, ZeroDivisionError):
            return 0.0

    def _enrich_transition_features(
        self,
        feature: Feature,
        history: List[Dict[str, Any]],
    ) -> Feature:
        """Add lagged transition features using only rows strictly before T."""
        from regime.regime_labeler import RegimeLabeler

        current = feature.to_dict()
        feature.price_return_1h = self._safe_return(feature.price, history, 1)
        feature.price_return_4h = self._safe_return(feature.price, history, 4)
        feature.price_return_12h = self._safe_return(feature.price, history, 12)

        feature.adx_4h_delta_3h = self._safe_delta(current, history, "adx_4h", 3)
        feature.adx_4h_delta_6h = self._safe_delta(current, history, "adx_4h", 6)
        feature.adx_4h_delta_12h = self._safe_delta(current, history, "adx_4h", 12)
        feature.di_spread_4h = round(feature.plus_di_4h - feature.minus_di_4h, 6)
        if len(history) >= 6:
            old_spread = float(history[-6].get("plus_di_4h") or 0) - float(
                history[-6].get("minus_di_4h") or 0
            )
            feature.di_spread_4h_delta_6h = round(
                feature.di_spread_4h - old_spread, 6
            )
        feature.macd_histogram_4h_delta_6h = self._safe_delta(
            current, history, "macd_histogram_4h", 6
        )
        feature.ema_gap_4h = round(feature.ema_12_4h - feature.ema_26_4h, 6)
        if len(history) >= 6:
            old_gap = float(history[-6].get("ema_12_4h") or 0) - float(
                history[-6].get("ema_26_4h") or 0
            )
            feature.ema_gap_4h_delta_6h = round(feature.ema_gap_4h - old_gap, 6)
        feature.atr_ratio_4h_1h_delta_6h = self._safe_delta(
            current, history, "atr_ratio_4h_1h", 6
        )
        feature.rsi_14_1h_delta_6h = self._safe_delta(
            current, history, "rsi_14_1h", 6
        )
        feature.bollinger_position_1d_delta_12h = self._safe_delta(
            current, history, "bollinger_position_1d", 12
        )

        feature.adx_range_margin = round(feature.adx_4h - 18.0, 6)
        feature.adx_trend_margin = round(feature.adx_4h - 20.0, 6)
        feature.atr_ratio_range_margin = round(feature.atr_ratio_4h_1h - 2.0, 6)

        signs = [
            1 if feature.plus_di_4h > feature.minus_di_4h else -1,
            1 if feature.ema_12_4h >= feature.ema_26_4h else -1,
            1 if feature.macd_histogram_4h >= 0 else -1,
            1 if feature.trend_continuation_4h >= 0 else -1,
        ]
        feature.rule_conflict_score = round(1.0 - abs(sum(signs)) / len(signs), 4)

        labeler = RegimeLabeler()
        regimes = [labeler.classify(row) for row in history[-24:]]
        current_regime = labeler.classify(feature.to_dict())
        sequence = regimes + [current_regime]
        age = 1
        for regime in reversed(sequence[:-1]):
            if regime != current_regime:
                break
            age += 1
        feature.regime_age_1h = age
        feature.regime_switches_24h = sum(
            int(a != b) for a, b in zip(sequence, sequence[1:])
        )
        feature.feature_schema_version = "transition_v1"
        feature.dynamic_features_ready = len(history) >= 12
        return feature

    async def process_async(self, before: int = None) -> int:
        """
        合并1小时、15分钟和4小时的特征参数（异步版本）
        """
        # before 为空时必须 sort_desc=True，否则 limit 会取到库中最老的 K 线
        sort_desc = before is None
        results = await asyncio.gather(
            async_candlestick_handler.get_candlestick_data(
                inst_id=self.inst_id, bar='1H', limit=self.rolling_norm_window,
                before=before, sort_desc=sort_desc,
            ),
            async_candlestick_handler.get_candlestick_data(
                inst_id=self.inst_id, bar='15m', limit=self.feature_window,
                before=before, sort_desc=sort_desc,
            ),
            async_candlestick_handler.get_candlestick_data(
                inst_id=self.inst_id, bar='4H', limit=self.feature_window,
                before=before, sort_desc=sort_desc,
            ),
            async_candlestick_handler.get_candlestick_data(
                inst_id=self.inst_id, bar='1D', limit=self.feature_window,
                before=before, sort_desc=sort_desc,
            ),
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
        candles1H = self._fetch_candles("1H", self.rolling_norm_window, before)
        candles15m = self._fetch_candles("15m", self.feature_window, before)
        candles4H = self._fetch_candles("4H", self.feature_window, before)
        candles1D = self._fetch_candles("1D", self.feature_window, before)
        
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
            # 必须走 _fetch_candles(before=None)：内部 sort_desc=True 取最近 K 线。
            # 若默认升序 limit，会拿到库中最老一段，导致多周期日期对不齐并返回 None。
            candles1H = self._fetch_candles("1H", self.rolling_norm_window, None)
            candles15m = self._fetch_candles("15m", self.feature_window, None)
            candles4H = self._fetch_candles("4H", self.feature_window, None)
            candles1D = self._fetch_candles("1D", self.feature_window, None)

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
                # Keep the live (confirm=0) bar for realtime prediction so
                # features reflect the current incomplete candle.
                timestamp = int(candle[0])
                dt = datetime.fromtimestamp(timestamp / 1000)
                
                converted_candle = {
                    "timestamp": timestamp,
                    "open": float(candle[1]),
                    "high": float(candle[2]),
                    "low": float(candle[3]),
                    "close": float(candle[4]),
                    "volume": float(candle[5]),
                    "confirm": int(candle[8]) if len(candle) > 8 else 1,
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
        
    def _common_process(
        self,
        candles1H: List[Dict[str, Any]],
        candles15m: List[Dict[str, Any]],
        candles4H: List[Dict[str, Any]],
        candles1D: List[Dict[str, Any]],
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Feature]:
        if candles1H is None or candles15m is None or candles4H is None or candles1D is None:
            log.warning(f"获取数据失败, 1H: {candles1H}, 15m: {candles15m}, 4H: {candles4H}, 1D: {candles1D}")
            return None
        fw = self.feature_window
        if len(candles1H) < fw or len(candles15m) < fw or len(candles4H) < fw or len(candles1D) < fw:
            log.warning(
                f"数据长度不足, 1H: {len(candles1H)} (need >={fw}), "
                f"15m: {len(candles15m)}, 4H: {len(candles4H)}, 1D: {len(candles1D)}"
            )
            return None

        candles1H_ind = candles1H[-fw:]
        
        try:
            last_1h = candles1H_ind[-1]
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
                # 用时间戳二次校验（避免 20~23 点 1H 与 16 点 4H 被误杀）
                ts_1h = last_1h.get('timestamp')
                ts_4h = last_4h.get('timestamp')
                if ts_1h is None or ts_4h is None:
                    log.warning("1H/4H 缺少 timestamp")
                    return None
                if ts_1h < ts_4h or ts_1h >= ts_4h + 4 * 60 * 60 * 1000:
                    log.warning(
                        "1H/4H 未对齐 ts_1h=%s ts_4h=%s hour_diff=%s",
                        ts_1h, ts_4h, hour_diff,
                    )
                    return None
            
            for i in range(fw - 1):
                if candles1H_ind[i+1].get('timestamp') != candles1H_ind[i].get('timestamp') + 60 * 60 * 1000:
                    log.warning(f"1H数据不连续, 索引: {i}, 时间差: {candles1H_ind[i+1].get('timestamp') - candles1H_ind[i].get('timestamp')}")
                    return None
            for i in range(fw - 1):
                if candles15m[i+1].get('timestamp') != candles15m[i].get('timestamp') + 15 * 60 * 1000:
                    log.warning(f"15m数据不连续, 索引: {i}, 时间差: {candles15m[i+1].get('timestamp') - candles15m[i].get('timestamp')}")
                    return None
            for i in range(fw - 1):
                if candles4H[i+1].get('timestamp') != candles4H[i].get('timestamp') + 4 * 60 * 60 * 1000:
                    log.warning(f"4H数据不连续, 索引: {i}, 时间差: {candles4H[i+1].get('timestamp') - candles4H[i].get('timestamp')}")
                    return None
            for i in range(fw - 1):
                if candles1D[i+1].get('timestamp') != candles1D[i].get('timestamp') + 24 * 60 * 60 * 1000:
                    log.warning(f"1D数据不连续, 索引: {i}, 时间差: {candles1D[i+1].get('timestamp') - candles1D[i].get('timestamp')}")
                    return None
                
        except (IndexError, KeyError) as e:
            log.warning(f"时间字段校验失败: {e}")
            return None
        
        norm_params = self._rolling_norm_params(candles1H)
        if not norm_params:
            log.warning("无法计算滚动归一化参数, timestamp=%s", candles1H_ind[-1].get('timestamp'))
            return None

        feature1h = Feature1HCreator(
            close_mean=norm_params['mean'],
            close_std=norm_params['std'],
            vol_mean=norm_params['vol_mean'],
            vol_std=norm_params['vol_std'],
        )
        feature15m = Feature15mCreator()
        feature4h = Feature4HCreator(
            close_mean=norm_params['mean'],
            close_std=norm_params['std'],
        )
        feature1D = Feature1DCreator(
            close_mean=norm_params['mean'],
            close_std=norm_params['std'],
        )
        
        feature1h_result = feature1h.calculate(candles1H_ind, candles15m)
        feature15m_result = feature15m.calculate(candles15m)
        feature4h_result = feature4h.calculate(candles4H, candles1H_ind)
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
            atr_ratio_1h_15m=feature1h_result.atr_ratio_1h_15m,
            rsi_divergence_1h=feature1h_result.rsi_divergence_1h,
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
            atr_ratio_4h_1h=feature4h_result.atr_ratio_4h_1h,
            rsi_divergence_4h=feature4h_result.rsi_divergence_4h,
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
        
        if history is None:
            history = feature_handler.get_feature_history(
                self.inst_id, before=feature.timestamp, bar="1H", limit=24
            )
        return self._enrich_transition_features(feature, history)
    
    def _process_and_cache(self, before: int = None):
        """
        处理单条数据并添加到缓存，当缓存达到 batch_size 时批量保存。
        Returns:
            (feature_timestamp, error_message)
        """
        fw = self.feature_window
        candles1H = self._fetch_candles("1H", self.rolling_norm_window, before)
        candles15m = self._fetch_candles("15m", fw, before)
        candles4H = self._fetch_candles("4H", fw, before)
        candles1D = self._fetch_candles("1D", fw, before)

        if not candles1H or not candles15m or not candles4H or not candles1D:
            return None, (
                f"K线为空 1H={len(candles1H)} 15m={len(candles15m)} "
                f"4H={len(candles4H)} 1D={len(candles1D)} before={before}"
            )

        if len(candles1H) < fw:
            return None, (
                f"1H 仅 {len(candles1H)} 根，需要 >={fw}；"
                f"请拉取至少 {self.rolling_norm_window} 根 1H K 线"
            )
        if len(candles15m) < fw or len(candles4H) < fw or len(candles1D) < fw:
            return None, (
                f"多周期 K 线不足 15m={len(candles15m)} 4H={len(candles4H)} "
                f"1D={len(candles1D)}，需要各 >={fw}"
            )

        features = self._common_process(
            candles1H=candles1H,
            candles15m=candles15m,
            candles4H=candles4H,
            candles1D=candles1D,
        )

        if not features:
            return None, (
                f"特征校验失败 ts={candles1H[-1].get('timestamp')} "
                f"(对齐/连续性/归一化)，详见服务日志"
            )

        self._batch_cache.append(features)

        if len(self._batch_cache) >= self.batch_size:
            self._flush_batch()

        return features.timestamp, None
    
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
          