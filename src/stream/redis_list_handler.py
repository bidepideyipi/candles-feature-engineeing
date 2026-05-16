"""
Redis List handler for processing filebeat messages and forwarding to Feishu.
"""

import logging
import json
import time
from typing import Optional, Dict, Any
import redis
from redis.exceptions import RedisError, ConnectionError

from config.settings import config
from utils.feishu_sender import feishu_sender

logger = logging.getLogger(__name__)


class RedisListHandler:
    """Handler for Redis List operations - processing filebeat messages."""
    
    def __init__(self,
                 redis_host: str = config.REDIS_HOST,
                 redis_port: int = config.REDIS_PORT,
                 redis_db: int = config.REDIS_DB,
                 list_name: str = "filebeat:notice"):
        self.redis_client: Optional[redis.Redis] = None
        self.list_name = list_name
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
            logger.info(f"Connected to Redis at {host}:{port}, db={db}, list={self.list_name}")
            return True
        except (RedisError, ConnectionError) as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self.redis_client = None
            return False
    
    def process_single_message(self) -> bool:
        """
        从 Redis list 中 LPOP 一条消息并发送到飞书
        
        Returns:
            bool: True if processed successfully, False otherwise
        """
        if self.redis_client is None:
            logger.warning("Redis not available, cannot process message")
            return False
        
        if feishu_sender is None:
            logger.warning("Feishu sender not available, cannot send message")
            return False
        
        try:
            message_str = self.redis_client.lpop(self.list_name)
            
            if not message_str:
                logger.debug(f"No message in Redis list: {self.list_name}")
                return False
            
            logger.info(f"Received message from Redis list: {self.list_name}")
            
            try:
                message_data = json.loads(message_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse message as JSON: {e}, message: {message_str[:200]}")
                return False
            
            message_content = message_data.get("message")
            
            if not message_content:
                logger.warning(f"Message does not contain 'message' field: {message_data}")
                return False
            
            
            logger.info(f"Extracted message content: {message_content[:100]}...")
            
            feishu_sender.send_message(message_content)
            
            logger.info(f"Successfully processed and sent message to Feishu")
            return True
            
        except RedisError as e:
            logger.error(f"Redis error while processing message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while processing message: {e}", exc_info=True)
            return False
    
    def start_continuous_processing(self, interval: float = 5.0):
        """
        持续监听 Redis list 并处理消息
        
        Args:
            interval: 检查间隔（秒）
        """
        logger.info(f"Starting continuous processing, interval: {interval}s")
        logger.info(f"Listening to Redis list: {self.list_name}")
        logger.info("Press Ctrl+C to stop")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                
                processed = self.process_single_message()
                
                if processed:
                    logger.info(f"Cycle #{cycle_count}: Message processed successfully")
                else:
                    logger.debug(f"Cycle #{cycle_count}: No message to process")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, stopping continuous processing...")
        except Exception as e:
            logger.error(f"Error in continuous processing: {e}", exc_info=True)
        
        logger.info("Continuous processing stopped")
    
    def get_list_length(self) -> int:
        """
        获取 Redis list 的长度
        
        Returns:
            int: list 长度
        """
        if self.redis_client is None:
            return 0
        try:
            length = self.redis_client.llen(self.list_name)
            return length
        except RedisError:
            return 0
    
    def is_connected(self) -> bool:
        """
        检查 Redis 连接状态
        
        Returns:
            bool: 是否已连接
        """
        if self.redis_client is None:
            return False
        try:
            self.redis_client.ping()
            return True
        except RedisError:
            return False


redis_list_handler = RedisListHandler()