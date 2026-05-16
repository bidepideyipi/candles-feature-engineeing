import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from stream.redis_list_handler import redis_list_handler

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_redis_list_handler():
    """测试 Redis List 处理器"""
    
    logger.info("=== Testing Redis List Handler ===")
    
    # 1. 检查 Redis 连接
    logger.info("Step 1: Checking Redis connection...")
    if not redis_list_handler.is_connected():
        logger.error("Redis is not connected, exiting...")
        return
    
    logger.info("Redis connected successfully")
    
    # 2. 检查 List 长度
    logger.info("Step 2: Checking Redis list length...")
    list_length = redis_list_handler.get_list_length()
    logger.info(f"Current list length: {list_length}")
    
    if list_length == 0:
        logger.warning("Redis list is empty, no messages to process")
        logger.info("To test, add a message to Redis:")
        logger.info("""
import redis
import json

r = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)
test_message = {
    "message": "Test notification from filebeat",
    "timestamp": 1234567890,
    "level": "info"
}
r.rpush("filebeat:notice", json.dumps(test_message))
        """)
        return
    
    # 3. 处理单条消息
    logger.info("Step 3: Processing single message...")
    success = redis_list_handler.process_single_message()
    if success:
        logger.info("Single message processed successfully")
    else:
        logger.warning("Failed to process single message")
    
    # 4. 再次处理下一条
    logger.info("Step 4: Processing next message (if available)...")
    success = redis_list_handler.process_single_message()
    if success:
        logger.info("Next message processed successfully")
    else:
        logger.info("No more messages")
    
    logger.info("=== Test completed ===")

if __name__ == "__main__":
    test_redis_list_handler()