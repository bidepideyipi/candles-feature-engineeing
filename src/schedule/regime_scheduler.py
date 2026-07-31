"""定时发布 regime 预测到 Redis。"""
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

from config.settings import config
from feature.feature_merge import FeatureMerge
from models.regime_trainer import regime_trainer
from stream.redis_stream_handler import redis_stream_handler
from utils.email_sender import email_sender

logger = logging.getLogger(__name__)


class RegimeScheduler:
    def __init__(self):
        self.interval_minutes = config.SCHEDULE_INTERVAL
        self.recipient = config.SCHEDULE_RECIPIENT
        self.from_local = config.SCHEDULE_DATA_SOURCE == "mongodb"

    def predict_regime(self) -> Optional[Dict[str, Any]]:
        if not regime_trainer.load_model():
            logger.error("Failed to load regime model")
            return None

        feature_merge = FeatureMerge()
        features = (
            feature_merge.quick_process_eth_from_mongodb()
            if self.from_local
            else feature_merge.quick_process_eth()
        )
        if features is None:
            logger.error("Failed to extract features for regime")
            return None

        payload = regime_trainer.build_prediction_payload(features)
        redis_meta = redis_stream_handler.publish_regime(payload)
        payload["redis"] = redis_meta
        return payload

    def run(self):
        logger.info("Regime scheduler started, interval=%s min", self.interval_minutes)
        cycle = 0
        while True:
            try:
                cycle += 1
                logger.info("=== Regime cycle #%s %s ===", cycle, datetime.now())
                payload = self.predict_regime()
                if payload:
                    redis_meta = payload.get("redis") or {}
                    logger.info(
                        "regime=%s strategy=%s confidence=%s reversal_alerted=%s",
                        payload.get("regime_label"),
                        payload.get("recommended_strategy"),
                        payload.get("confidence"),
                        redis_meta.get("reversal_alerted"),
                    )
                    # 仅趋势反转告警时发邮件（与 Stream XADD 一致）
                    if redis_meta.get("reversal_alerted"):
                        rev = redis_meta.get("reversal") or {}
                        try:
                            email_sender.send_trading_alert(
                                to_email=self.recipient,
                                prediction_data={
                                    "prediction_label": (
                                        f"REVERSAL {rev.get('from_regime_label')}→"
                                        f"{rev.get('to_regime_label')}"
                                    ),
                                    "prediction": payload.get("regime"),
                                    "probabilities": payload.get("probabilities"),
                                    "inst_id": payload.get("inst_id"),
                                    "price": payload.get("price"),
                                    "bar": "REGIME_REVERSAL",
                                },
                            )
                        except Exception as e:
                            logger.error("Regime reversal email failed: %s", e)
                time.sleep(self.interval_minutes * 60)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error("Regime scheduler error: %s", e, exc_info=True)
                time.sleep(self.interval_minutes * 60)


regime_scheduler = RegimeScheduler()
