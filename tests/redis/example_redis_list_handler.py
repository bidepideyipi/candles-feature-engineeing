import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from stream.redis_list_handler import RedisListHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def example_single_message():
    """示例：处理单条消息"""
    logger.info("示例 1: 处理单条消息")
    
    handler = RedisListHandler()
    
    if handler.process_single_message():
        logger.info("✓ 消息处理成功")
    else:
        logger.info("✗ 没有消息或处理失败")


def example_continuous_processing():
    """示例：持续监听处理"""
    logger.info("示例 2: 持续监听处理（按 Ctrl+C 停止）")
    
    handler = RedisListHandler()
    
    # 每 5 秒检查一次，每次只处理一条消息
    handler.start_continuous_processing(interval=5.0)


def example_check_status():
    """示例：检查状态"""
    logger.info("示例 3: 检查 Redis 和 List 状态")
    
    handler = RedisListHandler()
    
    # 检查连接
    if handler.is_connected():
        logger.info(f"✓ Redis 已连接")
    else:
        logger.error(f"✗ Redis 未连接")
        return
    
    # 检查 List 长度
    length = handler.get_list_length()
    logger.info(f"✓ List 'filebeat:notice' 长度: {length}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Redis List Handler 使用示例')
    parser.add_argument(
        '--mode',
        choices=['single', 'continuous', 'check'],
        default='check',
        help='运行模式'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'single':
        example_single_message()
    elif args.mode == 'continuous':
        example_continuous_processing()
    elif args.mode == 'check':
        example_check_status()