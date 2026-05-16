import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from utils.feishu_sender import FeishuSender
from collect.config_handler import config_handler

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_feishu_sender():
    logger.info("=== Testing Feishu Sender ===")
    
    # 1. Check configuration
    logger.info("Step 1: Checking MongoDB configuration...")
    config = config_handler.get_config_dict("feishu")
    if config:
        logger.info(f"Config found: {config}")
    else:
        logger.error("No configuration found in MongoDB for 'feishu'")
        logger.info("Please run the following to add configuration:")
        logger.info("""
from collect.config_handler import config_handler

config_handler.save_config(item="feishu", key="app_id", value="your_app_id")
config_handler.save_config(item="feishu", key="app_secret", value="your_app_secret")
config_handler.save_config(item="feishu", key="receive_id", value="your_chat_id")
config_handler.save_config(item="feishu", key="receive_id_type", value="chat_id")
        """)
        return
    
    # 2. Initialize sender
    logger.info("Step 2: Initializing FeishuSender...")
    sender = FeishuSender()
    
    if sender is None:
        logger.error("Failed to initialize FeishuSender")
        return
    
    # 3. Send test message
    logger.info("Step 3: Sending test message...")
    try:
        sender.send_message("test content")
        logger.info("=== Test completed successfully ===")
    except Exception as e:
        logger.error(f"Test failed with exception: {e}", exc_info=True)

if __name__ == "__main__":
    test_feishu_sender()
