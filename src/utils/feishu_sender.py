import json

import logging
logger = logging.getLogger(__name__)
import lark_oapi as lark
from lark_oapi.api.im.v1 import *

from collect.config_handler import config_handler

class FeishuSender:
    """
    飞书消息发送器
    """
    def __init__(self, config_item: str = "feishu"):
        logger.info(f"Initializing FeishuSender with config_item: {config_item}")
        
        config = config_handler.get_config_dict(config_item)
        logger.info(f"Config retrieved: {config}")
        
        if not config:
            logger.error(f"Feishu configuration not found: {config_item}")
            return None
        
        app_id = config.get("app_id")
        app_secret = config.get("app_secret")
        self.receive_id_type = config.get("receive_id_type")
        self.receive_id = config.get("receive_id")
        
        logger.info(f"Config values - app_id: {app_id}, receive_id: {self.receive_id}, receive_id_type: {self.receive_id_type}")
        
        if not app_id or not app_secret or not self.receive_id or not self.receive_id_type:
            logger.error(f"Feishu configuration incomplete. Required: app_id, app_secret, receive_id, receive_id_type")
            logger.error(f"Missing values: app_id={bool(app_id)}, app_secret={bool(app_secret)}, receive_id={bool(self.receive_id)}, receive_id_type={bool(self.receive_id_type)}")
            return None
        
        try:
            logger.info("Building Lark client...")
            self.client = lark.Client.builder() \
                .app_id(app_id) \
                .app_secret(app_secret) \
                .log_level(lark.LogLevel.DEBUG) \
                .build()
            logger.info("Lark client built successfully")
        except Exception as e:
            logger.error(f"Failed to build Lark client: {e}", exc_info=True)
            return None
            
    def send_message(self, message: str):
        """
        发送消息到指定的飞书聊天室
        """
        logger.info(f"Attempting to send message: {message}")
        
        if not self.client:
            logger.error("Feishu client not initialized, cannot send message")
            return
        
        try:
            logger.info(f"Creating message request to {self.receive_id} (type: {self.receive_id_type})")
            request: CreateMessageRequest = CreateMessageRequest.builder() \
                .receive_id_type(self.receive_id_type) \
                .request_body(CreateMessageRequestBody.builder()
                    .receive_id(self.receive_id)
                    .msg_type("text")
                    .content(f"{{\"text\":\"{message}\"}}")
                    .build()) \
                .build()
            
            logger.info("Sending message to Lark API...")
            response: CreateMessageResponse = self.client.im.v1.message.create(request)
            logger.info(f"Response received - success: {response.success()}, code: {response.code}, msg: {response.msg}")
            
            if not response.success():
                logger.error(
                    f"client.im.v1.message.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
                return
            logger.info(f"Message sent successfully! Response data: {lark.JSON.marshal(response.data, indent=4)}")
        except Exception as e:
            logger.error(f"Exception while sending message: {e}", exc_info=True)
        
# Global instance - will be None if initialization fails
feishu_sender = FeishuSender()
if feishu_sender is None:
    logger.warning("FeishuSender failed to initialize, feishu_sender is None")
