"""
Redis handler: 当前 regime 用 SET；滑动窗口 ZSET 检测趋势反转后才 XADD 告警。
"""

import json
import logging
from typing import Any, Dict, List, Optional

import redis
from redis.exceptions import ConnectionError, RedisError

from config.settings import config
from regime.regime_types import REGIME_LABELS, MarketRegime

logger = logging.getLogger(__name__)

# 仅 UP ↔ DOWN 视为趋势反转；RANGE 不参与方向判定
_DIRECTIONAL = {int(MarketRegime.TREND_UP), int(MarketRegime.TREND_DOWN)}


class RedisStreamHandler:
    """Redis：current key + zset 窗口；反转时写 Stream。"""

    def __init__(
        self,
        redis_host: str = config.REDIS_HOST,
        redis_port: int = config.REDIS_PORT,
        redis_db: int = config.REDIS_DB,
        stream_name: str = config.REDIS_SIGNAL_STREAM,
    ):
        self.redis_client: Optional[redis.Redis] = None
        self.stream_name = stream_name
        self._connect_redis(redis_host, redis_port, redis_db)

    def _connect_redis(self, host: str, port: int, db: int) -> bool:
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            self.redis_client.ping()
            logger.info("Connected to Redis at %s:%s, db=%s", host, port, db)
            return True
        except (RedisError, ConnectionError) as e:
            logger.warning("Failed to connect to Redis: %s", e)
            self.redis_client = None
            return False

    @staticmethod
    def _current_key(inst_id: str) -> str:
        return f"{config.REDIS_REGIME_CURRENT_PREFIX}:{inst_id}"

    @staticmethod
    def _zwin_key(inst_id: str) -> str:
        return f"{config.REDIS_REGIME_ZWIN_PREFIX}:{inst_id}"

    @staticmethod
    def _last_reversal_key(inst_id: str) -> str:
        return f"{config.REDIS_REGIME_LAST_REVERSAL_PREFIX}:{inst_id}"

    @staticmethod
    def _last_transition_key(inst_id: str) -> str:
        return f"{config.REDIS_REGIME_LAST_REVERSAL_PREFIX}:transition:{inst_id}"

    def publish_regime(self, regime_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        1) SET 当前趋势到 regime:current:{inst_id}
        2) ZADD 滑动窗口并裁剪
        3) 仅当检测到 UP↔DOWN 反转（且达到确认次数）时 XADD 到 regime stream

        Returns:
            写入结果摘要（供 API 透出）
        """
        result: Dict[str, Any] = {
            "updated_current": False,
            "window_size": 0,
            "reversal_detected": False,
            "reversal_alerted": False,
            "transition_alerted": False,
            "transition_stream_id": None,
            "stream_id": None,
            "reversal": None,
            "error": None,
        }
        if self.redis_client is None:
            result["error"] = "Redis not available"
            logger.warning("Redis not available, skipping regime publish")
            return result

        try:
            inst_id = regime_data.get("inst_id", "ETH-USDT-SWAP")
            ts = int(regime_data.get("timestamp") or 0)
            if ts <= 0:
                result["error"] = "invalid timestamp"
                logger.error("publish_regime: invalid timestamp in %s", regime_data)
                return result

            present = regime_data.get("present") or {}
            outlook = (
                regime_data.get("outlook_48h")
                or regime_data.get("outlook")
                or regime_data.get("transition")
                or {}
            )
            derived = regime_data.get("derived") or {}

            # Prefer explicit present; fall back to flat legacy fields
            present_regime = int(
                present.get("regime")
                or regime_data.get("regime")
                or 0
            )
            present_label = present.get("regime_label") or regime_data.get(
                "regime_label", ""
            )
            # Transition model: confidence = P(change) when available
            confidence = float(
                derived.get("p_change")
                if derived.get("p_change") is not None
                else outlook.get("p_change")
                if outlook.get("p_change") is not None
                else outlook.get("confidence")
                if outlook.get("confidence") is not None
                else regime_data.get("confidence")
                or 0
            )
            outlook_regime = int(
                outlook.get("regime") or present_regime or regime_data.get("regime") or 0
            )
            outlook_label = outlook.get("regime_label") or outlook.get("prediction") or ""

            current_payload = {
                "type": "regime",
                "timestamp": ts,
                "inst_id": inst_id,
                "bar": regime_data.get("bar", "1H"),
                "price": regime_data.get("price"),
                "horizon_hours": regime_data.get("horizon_hours"),
                "present": present
                or {
                    "regime": present_regime,
                    "regime_label": present_label,
                    "source": "rules",
                },
                "transition": regime_data.get("transition") or outlook,
                "outlook_48h": outlook
                if outlook.get("regime") is not None
                else None,
                "derived": derived
                or {
                    "continues": present_regime == outlook_regime,
                    "changes": present_regime != outlook_regime,
                },
            }
            # Drop null outlook_48h key noise
            if current_payload.get("outlook_48h") is None:
                current_payload.pop("outlook_48h", None)

            # ---- 1. SET dual-track snapshot ----
            current_key = self._current_key(inst_id)
            self.redis_client.set(
                current_key, json.dumps(current_payload, ensure_ascii=False)
            )
            result["updated_current"] = True

            # ---- 2. ZADD window using PRESENT regime (structure now) ----
            zkey = self._zwin_key(inst_id)
            member = json.dumps(
                {
                    "timestamp": ts,
                    "regime": present_regime,
                    "regime_label": present_label,
                    # Present regime is deterministic rules; do not gate reversal
                    # detection with transition-model P(change).
                    "confidence": 1.0,
                    "p_change": confidence,
                    "outlook_regime": outlook_regime,
                    "outlook_label": outlook_label,
                    "continues": current_payload["derived"].get("continues"),
                    "price": current_payload.get("price"),
                    "recommended_strategy": (present or {}).get(
                        "recommended_strategy", ""
                    ),
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            # 同一 timestamp 只保留一条
            old_at_ts = self.redis_client.zrangebyscore(zkey, ts, ts)
            if old_at_ts:
                self.redis_client.zrem(zkey, *old_at_ts)
            self.redis_client.zadd(zkey, {member: ts})

            window_ms = max(1, config.REDIS_REGIME_WINDOW_HOURS) * 60 * 60 * 1000
            cutoff = ts - window_ms
            self.redis_client.zremrangebyscore(zkey, "-inf", cutoff)

            raw_members = self.redis_client.zrange(zkey, 0, -1)
            window_points = self._parse_window_members(raw_members)
            result["window_size"] = len(window_points)

            # ---- 3. Model transition alert: only after holdout gate passes ----
            transition = current_payload.get("transition") or {}
            if transition.get("alert_eligible"):
                transition_id = f"{ts}:{transition.get('horizon_hours')}"
                transition_key = self._last_transition_key(inst_id)
                if self.redis_client.get(transition_key) != transition_id:
                    transition_message = {
                        "type": "regime_change_risk",
                        "timestamp": str(ts),
                        "inst_id": inst_id,
                        "bar": str(current_payload.get("bar", "1H")),
                        "horizon_hours": str(
                            transition.get("horizon_hours") or ""
                        ),
                        "p_change": str(transition.get("p_change") or 0),
                        "threshold": str(transition.get("threshold") or ""),
                        "present": json.dumps(
                            current_payload.get("present") or {},
                            ensure_ascii=False,
                        ),
                        "transition": json.dumps(
                            transition, ensure_ascii=False
                        ),
                    }
                    transition_stream_id = self.redis_client.xadd(
                        config.REDIS_REGIME_STREAM, transition_message
                    )
                    self.redis_client.set(transition_key, transition_id)
                    result["transition_alerted"] = True
                    result["transition_stream_id"] = transition_stream_id

            # ---- 4. Present-regime reversal detection → conditional XADD ----
            reversal = self._detect_trend_reversal(window_points)
            if not reversal:
                logger.info(
                    "Regime current set %s; window=%s; no reversal",
                    current_key,
                    result["window_size"],
                )
                return result

            result["reversal_detected"] = True
            result["reversal"] = reversal

            alert_id = (
                f"{reversal['from_regime']}:{reversal['to_regime']}:"
                f"{reversal['streak_start_ts']}"
            )
            last_key = self._last_reversal_key(inst_id)
            if self.redis_client.get(last_key) == alert_id:
                logger.info("Reversal already alerted: %s", alert_id)
                return result

            stream_message = {
                "type": "regime_reversal",
                "timestamp": str(ts),
                "inst_id": inst_id,
                "bar": str(current_payload.get("bar", "1H")),
                "from_regime": str(reversal["from_regime"]),
                "from_regime_label": reversal["from_regime_label"],
                "to_regime": str(reversal["to_regime"]),
                "to_regime_label": reversal["to_regime_label"],
                "confirm_count": str(reversal["confirm_count"]),
                "streak_start_ts": str(reversal["streak_start_ts"]),
                "confidence": str(confidence),
                "price": str(current_payload.get("price") or ""),
                "present": json.dumps(current_payload.get("present") or {}),
                "transition": json.dumps(current_payload.get("transition") or {}),
                "derived": json.dumps(current_payload.get("derived") or {}),
                "current": json.dumps(current_payload, ensure_ascii=False),
            }
            stream = config.REDIS_REGIME_STREAM
            message_id = self.redis_client.xadd(stream, stream_message)
            self.redis_client.set(last_key, alert_id)
            result["reversal_alerted"] = True
            result["stream_id"] = message_id
            logger.info(
                "Regime reversal alerted to %s id=%s %s→%s",
                stream,
                message_id,
                reversal["from_regime_label"],
                reversal["to_regime_label"],
            )
            return result
        except RedisError as e:
            result["error"] = str(e)
            logger.error("Failed to publish regime: %s", e)
            return result

    @staticmethod
    def _parse_window_members(raw_members: List[str]) -> List[Dict[str, Any]]:
        points: List[Dict[str, Any]] = []
        for raw in raw_members:
            try:
                obj = json.loads(raw)
                points.append(
                    {
                        "timestamp": int(obj.get("timestamp", 0)),
                        "regime": int(obj.get("regime", 0)),
                        "regime_label": obj.get("regime_label", ""),
                        "confidence": float(obj.get("confidence", 0) or 0),
                        "price": obj.get("price"),
                        "recommended_strategy": obj.get("recommended_strategy", ""),
                    }
                )
            except (TypeError, ValueError, json.JSONDecodeError) as e:
                logger.warning("Skip bad zwin member: %s (%s)", raw, e)
        points.sort(key=lambda p: p["timestamp"])
        return points

    def _detect_trend_reversal(
        self, window_points: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        在置信度过滤后的方向序列上：末尾连续 confirm 次为方向 A，
        且 streak 前一方向为相反的 UP/DOWN → 判定反转。
        """
        min_conf = float(config.REDIS_REGIME_MIN_CONFIDENCE)
        confirm = max(1, int(config.REDIS_REGIME_REVERSAL_CONFIRM))

        directional = [
            p
            for p in window_points
            if int(p["regime"]) in _DIRECTIONAL and float(p["confidence"]) >= min_conf
        ]
        if len(directional) < confirm + 1:
            return None

        curr = int(directional[-1]["regime"])
        streak = 1
        for i in range(len(directional) - 2, -1, -1):
            if int(directional[i]["regime"]) == curr:
                streak += 1
            else:
                break
        if streak < confirm:
            return None

        before_idx = len(directional) - streak - 1
        if before_idx < 0:
            return None
        prev = int(directional[before_idx]["regime"])
        if prev not in _DIRECTIONAL or prev == curr:
            return None

        streak_start_ts = int(directional[-streak]["timestamp"])
        try:
            from_label = REGIME_LABELS[MarketRegime(prev)]
            to_label = REGIME_LABELS[MarketRegime(curr)]
        except ValueError:
            from_label = str(prev)
            to_label = str(curr)

        return {
            "from_regime": prev,
            "from_regime_label": from_label,
            "to_regime": curr,
            "to_regime_label": to_label,
            "confirm_count": streak,
            "streak_start_ts": streak_start_ts,
        }

    def publish_prediction(self, prediction_data: Dict[str, Any]) -> bool:
        if self.redis_client is None:
            logger.warning("Redis not available, skipping stream publish")
            return False

        try:
            message = {
                "timestamp": prediction_data.get("timestamp", 0),
                "inst_id": prediction_data.get("inst_id", "ETH-USDT-SWAP"),
                "bar": prediction_data.get("bar", "1H"),
                "prediction": prediction_data.get("prediction", 0),
                "prediction_label": prediction_data.get("prediction_label", ""),
                "prediction_high": prediction_data.get("prediction_high", 0),
                "prediction_high_label": prediction_data.get("prediction_high_label", ""),
                "prediction_low": prediction_data.get("prediction_low", 0),
                "prediction_low_label": prediction_data.get("prediction_low_label", ""),
                "probabilities": json.dumps(prediction_data.get("probabilities", {})),
                "probabilities_high": json.dumps(
                    prediction_data.get("probabilities_high", {})
                ),
                "probabilities_low": json.dumps(
                    prediction_data.get("probabilities_low", {})
                ),
                "features_count": prediction_data.get("features_count", 0),
                "price": str(prediction_data.get("price")),
                "line1": "0.012",
                "line2": "0.036",
            }

            message_id = self.redis_client.xadd(self.stream_name, message)
            logger.info(
                "Published prediction to Redis Stream: %s, message_id: %s",
                self.stream_name,
                message_id,
            )
            return True
        except RedisError as e:
            logger.error("Failed to publish to Redis Stream: %s", e)
            return False

    def get_stream_length(self) -> int:
        if self.redis_client is None:
            return 0
        try:
            info = self.redis_client.xinfo_stream(self.stream_name)
            return info.get("length", 0)
        except RedisError:
            return 0

    def is_connected(self) -> bool:
        if self.redis_client is None:
            return False
        try:
            self.redis_client.ping()
            return True
        except RedisError:
            return False


redis_stream_handler = RedisStreamHandler()
