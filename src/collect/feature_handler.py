"""
Feature data handler for MongoDB operations.
Handles feature data storage and retrieval.
"""

import logging
from typing import List, Dict, Any

from config.settings import config
from .mongodb_base import MongoDBBaseHandler

logger = logging.getLogger(__name__)

class FeatureDataHandler(MongoDBBaseHandler):
    """Handler for feature data operations."""
    
    def __init__(self):
        super().__init__()
        self.collection_name = config.MONGODB_COLLECTIONS['features']
    
    def save_features(self, features_data: List[Dict[str, Any]]) -> bool:
        """
        Save calculated features to MongoDB features collection.
        
        Args:
            features_data: List of feature dictionaries
            
        Returns:
            bool: True if save successful, False otherwise
        """
        if not features_data:
            logger.warning("No feature data to save")
            return True
            
        try:
            collection = self._get_collection()
            if collection is None:
                return False
            
            result = collection.insert_many(features_data)
            logger.info(f"Saved {len(result.inserted_ids)} feature records")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save features: {e}")
            return False
    
    def get_features(self, limit: int = 1000, inst_id: str = None, bar: str = None) -> List[Dict[str, Any]]:
        """
        Retrieve feature data.
        
        Args:
            limit: Maximum number of records to retrieve
            inst_id: Instrument ID to filter by
            bar: Time interval to filter by
            
        Returns:
            List of feature data
        """
        try:
            collection = self._get_collection()
            if collection is None:
                return []
            
            # Build query filter
            query = {}
            if inst_id:
                query["inst_id"] = inst_id
            if bar:
                query["bar"] = bar
            
            cursor = collection.find(query).sort("timestamp", -1).limit(limit)
            return list(cursor)
            
        except Exception as e:
            logger.error(f"Failed to retrieve features: {e}")
            return []

# Global instance
feature_handler = FeatureDataHandler()