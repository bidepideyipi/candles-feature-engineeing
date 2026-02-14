"""
Configuration handler for MongoDB operations.
Handles configuration data storage and retrieval.
"""

import logging
from typing import Dict, Any, List, Optional
from pymongo import UpdateOne

from config.settings import config
from .mongodb_base import MongoDBBaseHandler

logger = logging.getLogger(__name__)


class ConfigHandler(MongoDBBaseHandler):
    """Handler for configuration data operations."""
    
    def __init__(self):
        super().__init__()
        self.collection_name = config.MONGODB_COLLECTIONS['config']
        self._create_indexes([
            ('item', False),
            ('key', False),
            (('item', 'key'), True)  # Unique composite index
        ])
    
    def save_config(self, item: str, key: str, value: str, desc: str = "") -> bool:
        """
        Save configuration data to MongoDB with upsert capability.
        
        Args:
            item: Configuration item (e.g., "smtp.qq.com")
            key: Configuration key (e.g., "account", "authCode")
            value: Configuration value
            desc: Description of the configuration
            
        Returns:
            bool: True if save successful, False otherwise
        """
        try:
            collection = self._get_collection()
            if collection is None:
                return False
            
            result = collection.update_one(
                {
                    "item": item,
                    "key": key
                },
                {
                    "$set": {
                        "item": item,
                        "key": key,
                        "value": value,
                        "desc": desc
                    }
                },
                upsert=True
            )
            
            if result.upserted_id is not None:
                logger.info(f"Inserted new config: {item}.{key}")
            else:
                logger.info(f"Updated existing config: {item}.{key}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def get_config(self, item: str, key: str) -> Optional[str]:
        """
        Get configuration value by item and key.
        
        Args:
            item: Configuration item (e.g., "smtp.qq.com")
            key: Configuration key (e.g., "account", "authCode")
            
        Returns:
            Configuration value or None if not found
        """
        try:
            collection = self._get_collection()
            if collection is None:
                return None
            
            config_doc = collection.find_one({
                "item": item,
                "key": key
            })
            
            if config_doc:
                return config_doc.get("value")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get config: {e}")
            return None
    
    def get_config_dict(self, item: str) -> Dict[str, str]:
        """
        Get all configurations for a specific item.
        
        Args:
            item: Configuration item (e.g., "smtp.qq.com")
            
        Returns:
            Dictionary of key-value pairs for the item
        """
        try:
            collection = self._get_collection()
            if collection is None:
                return {}
            
            configs = collection.find({"item": item})
            return {doc["key"]: doc["value"] for doc in configs}
            
        except Exception as e:
            logger.error(f"Failed to get config dict: {e}")
            return {}
    
    def delete_config(self, item: str, key: str) -> bool:
        """
        Delete configuration by item and key.
        
        Args:
            item: Configuration item (e.g., "smtp.qq.com")
            key: Configuration key (e.g., "account", "authCode")
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            collection = self._get_collection()
            if collection is None:
                return False
            
            result = collection.delete_one({
                "item": item,
                "key": key
            })
            
            if result.deleted_count > 0:
                logger.info(f"Deleted config: {item}.{key}")
                return True
            else:
                logger.warning(f"Config not found: {item}.{key}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to delete config: {e}")
            return False
    
    def list_configs(self, item: str = None) -> List[Dict[str, Any]]:
        """
        List all configurations, optionally filtered by item.
        
        Args:
            item: Optional filter by item
            
        Returns:
            List of configuration documents
        """
        try:
            collection = self._get_collection()
            if collection is None:
                return []
            
            query = {}
            if item:
                query["item"] = item
            
            configs = list(collection.find(query, {"_id": 0}))
            return configs
            
        except Exception as e:
            logger.error(f"Failed to list configs: {e}")
            return []


# Global instance
config_handler = ConfigHandler()
