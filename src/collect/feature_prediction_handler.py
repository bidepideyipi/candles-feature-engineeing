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

class FeatureDataPredictionHandler(MongoDBBaseHandler):
    """Handler for feature data operations."""
    
    def __init__(self):
        super().__init__()
        self.collection_name = config.MONGODB_COLLECTIONS['features_prediction']
        self._create_indexes([
            ('timestamp', False),
            ('inst_id', False),
            ('bar', False),
            (('inst_id', 'timestamp', 'bar'), True)
        ])
    
    def save_feature(self, feature_data: Dict[str, Any], ts: int = None) -> bool:
        """
        Save calculated feature to MongoDB features collection.
        
        Args:
            feature_data: Feature dictionary
            
        Returns:
            bool: True if save successful, False otherwise
        """
        if not feature_data:
            logger.warning("No feature data to save")
            return True
            
        try:
            collection = self._get_collection()
            if collection is None:
                return False
            
            feature_data["timestamp"] = ts
            result = collection.insert_one(feature_data)
            logger.info(f"Saved feature record with id: {result.inserted_id}")
            return True
            
        except DuplicateKeyError:
            logger.warning(f"Duplicate key error: feature already exists")
            return True
        except Exception as e:
            logger.error(f"Failed to save feature: {e}")
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
    
    def update_feature_label(self, inst_id: str, timestamp: int, label: int, label_high: int, label_low: int) -> bool:
        """
        Update the label of a feature record.
        
        Args:
            inst_id: Instrument ID
            timestamp: Timestamp of the feature
            label: Classification label
            label_name: Name of the label field to update (default: "label")
            
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
                "$set": {
                    "label": label,
                    "label_high": label_high,
                    "label_low": label_low
                }
            }
            
            result = collection.update_one(query, update)
            
            if result.modified_count > 0:
                logger.info(f"Updated label for inst_id: {inst_id}, timestamp: {timestamp}, label: {label}, label_high: {label_high}, label_low: {label_low}")
                return True
            else:
                logger.warning(f"No record found or no update needed for inst_id: {inst_id}, timestamp: {timestamp}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update feature label: {e}")
            return False
    
    def update_feature_prediction_label(self, inst_id: str, timestamp: int, label: int, label_high: int, label_low: int) -> bool:
        """
        这里存入的是预测的标签，用于和最终的标签进行对比分析
        Update the label_prediction of a feature record.
        
        Args:
            inst_id: Instrument ID
            timestamp: Timestamp of the feature
            label: Classification label
            label_name: Name of the label field to update (default: "label")
            
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
                "$set": {
                    "label_prediction": label,
                    "label_prediction_high": label_high,
                    "label_prediction_low": label_low
                }
            }
            
            result = collection.update_one(query, update)
            
            if result.modified_count > 0:
                logger.info(f"Updated label_prediction for inst_id: {inst_id}, timestamp: {timestamp}, label_prediction: {label}, label_prediction_high: {label_high}, label_prediction_low: {label_low}")
                return True
            else:
                logger.warning(f"No record found or no update needed for inst_id: {inst_id}, timestamp: {timestamp}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update feature label: {e}")
            return False

# Global instance
feature_pr_handler = FeatureDataPredictionHandler()
