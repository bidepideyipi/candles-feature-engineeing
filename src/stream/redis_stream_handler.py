"""
Redis Stream handler for publishing prediction signals.
"""

import logging
import json
from typing import Dict, Any, Optional
import redis
from redis.exceptions import RedisError, ConnectionError

from config.settings import config

logger = logging.getLogger(__name__)


class RedisStreamHandler:
    """Handler for Redis Stream operations."""
    
    def __init__(self,
                 redis_host: str = config.REDIS_HOST,
                 redis_port: int = config.REDIS_PORT,
                 redis_db: int = config.REDIS_DB,
                 stream_name: str = config.REDIS_SIGNAL_STREAM):
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
                socket_timeout=5
            )
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {host}:{port}, db={db}")
            return True
        except (RedisError, ConnectionError) as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self.redis_client = None
            return False
    
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
                "probabilities_high": json.dumps(prediction_data.get("probabilities_high", {})),
                "probabilities_low": json.dumps(prediction_data.get("probabilities_low", {})),
                "features_count": prediction_data.get("features_count", 0),
                "price": prediction_data.get("price")
                
            }
            
            message_id = self.redis_client.xadd(self.stream_name, message)
            logger.info(f"Published prediction to Redis Stream: {self.stream_name}, message_id: {message_id}")
            return True
        except RedisError as e:
            logger.error(f"Failed to publish to Redis Stream: {e}")
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
