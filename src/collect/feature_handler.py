"""
Feature data handler for MongoDB operations.
Handles feature data storage and retrieval.
"""

import logging
from typing import List, Dict, Any
from pymongo.errors import DuplicateKeyError, BulkWriteError

from config.settings import config
from .mongodb_base import MongoDBBaseHandler

logger = logging.getLogger(__name__)

class FeatureDataHandler(MongoDBBaseHandler):
    """Handler for feature data operations."""
    
    def __init__(self):
        super().__init__()
        self.collection_name = config.MONGODB_COLLECTIONS['features']
        self._create_indexes([
            ('timestamp', False),
            ('inst_id', False),
            ('bar', False),
            (('inst_id', 'timestamp', 'bar'), True)
        ])
    
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
            
        except DuplicateKeyError:
            logger.warning(f"Duplicate key error: some features already exist")
            return True
        except BulkWriteError as e:
            # Check if it's a duplicate key error in bulk operation
            if 'duplicate key' in str(e.details).lower():
                logger.warning(f"Duplicate key error in bulk insert: some features already exist")
                return True
            logger.error(f"Failed to save features (bulk write error): {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to save features: {e}")
            return False
    
    def get_features(self, limit: int = 1000, inst_id: str = None, bar: str = None, isNull: bool = False) -> List[Dict[str, Any]]:
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
            if isNull:
                query["label"] = None
            
            cursor = collection.find(query).sort("timestamp", -1).limit(limit)
            return list(cursor)
            
        except Exception as e:
            logger.error(f"Failed to retrieve features: {e}")
            return []
    
    def update_feature_label(self, inst_id: str, timestamp: int, label: int) -> bool:
        """
        Update the label of a feature record.
        
        Args:
            inst_id: Instrument ID
            timestamp: Timestamp of the feature
            label: Classification label
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            collection = self._get_collection()
            if collection is None:
                return False
            
            query = {
                "inst_id": inst_id,
                "timestamp": timestamp
            }
            
            update = {
                "$set": {"label": label}
            }
            
            result = collection.update_one(query, update)
            
            if result.modified_count > 0:
                logger.info(f"Updated label for inst_id: {inst_id}, timestamp: {timestamp}, label: {label}")
                return True
            else:
                logger.warning(f"No record found or no update needed for inst_id: {inst_id}, timestamp: {timestamp}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update feature label: {e}")
            return False

# Global instance
feature_handler = FeatureDataHandler()