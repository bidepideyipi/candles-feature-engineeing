"""
Feature data handler for MongoDB operations.
Handles feature data storage and retrieval.
"""

import logging
from typing import List, Dict, Any, Union, Optional
from pymongo.errors import DuplicateKeyError, BulkWriteError

from config.settings import config
from .mongodb_base import MongoDBBaseHandler
from feature.feature_types import Feature

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
    
    def save_features(self, features_data: Union[List[Dict[str, Any]], List[Feature]]) -> bool:
        """
        Save calculated features to MongoDB features collection.
        
        Args:
            features_data: List of feature dictionaries or Feature objects
            
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
            
            # Convert Feature objects to dicts if needed
            data_to_save = []
            for item in features_data:
                if isinstance(item, Feature):
                    data_to_save.append(item.to_dict())
                else:
                    data_to_save.append(item)
            
            result = collection.insert_many(data_to_save)
            logger.info(f"Saved {len(result.inserted_ids)} feature records")
            return True
            
        except DuplicateKeyError:
            logger.warning(f"Duplicate key error: some features already exist")
            return True
        except BulkWriteError as e:
            if 'duplicate key' in str(e.details).lower():
                logger.warning(f"Duplicate key error in bulk insert: some features already exist")
                return True
            logger.error(f"Failed to save features (bulk write error): {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to save features: {e}")
            return False
    
    def get_features(self, limit: int = 1000, inst_id: str = None, bar: str = None, isNull: bool = False, as_model: bool = False) -> Union[List[Dict[str, Any]], List[Feature]]:
        """
        Retrieve feature data.
        
        Args:
            limit: Maximum number of records to retrieve
            inst_id: Instrument ID to filter by
            bar: Time interval to filter by
            isNull: Filter for records with null label
            as_model: Return as List[Feature] instead of List[Dict]
            
        Returns:
            List of feature data (Dict or Feature objects)
        """
        try:
            collection = self._get_collection()
            if collection is None:
                return []
            
            query = {}
            if inst_id:
                query["inst_id"] = inst_id
            if bar:
                query["bar"] = bar
            if isNull:
                query["label"] = None
            
            cursor = collection.find(query).sort("timestamp", -1).limit(limit)
            docs = list(cursor)
            
            if as_model:
                return [Feature.from_dict(doc) for doc in docs]
            return docs
            
        except Exception as e:
            logger.error(f"Failed to retrieve features: {e}")
            return []
    
    def get_feature(self, inst_id: str, timestamp: int, as_model: bool = False) -> Optional[Union[Dict[str, Any], Feature]]:
        """
        Get a single feature by inst_id and timestamp.
        
        Args:
            inst_id: Instrument ID
            timestamp: Timestamp of the feature
            as_model: Return as Feature instead of Dict
            
        Returns:
            Feature data or None
        """
        try:
            collection = self._get_collection()
            if collection is None:
                return None
            
            query = {
                "inst_id": inst_id,
                "timestamp": timestamp
            }
            
            doc = collection.find_one(query)
            
            if doc and as_model:
                return Feature.from_dict(doc)
            return doc
            
        except Exception as e:
            logger.error(f"Failed to retrieve feature: {e}")
            return None
    
    def update_feature_label(self, inst_id: str, timestamp: int, label: int, label_high: int, label_low: int) -> bool:
        """
        Update the label of a feature record.
        
        Args:
            inst_id: Instrument ID
            timestamp: Timestamp of the feature
            label: Classification label
            label_high: High price label
            label_low: Low price label
            
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

feature_handler = FeatureDataHandler()