"""
Feature data handler for MongoDB operations.
Handles feature data storage and retrieval.
"""

import logging
from typing import List, Dict, Any, Union, Optional
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError

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
            
            data_to_save = []
            for item in features_data:
                if isinstance(item, Feature):
                    data_to_save.append(item.to_dict())
                else:
                    data_to_save.append(item)

            bulk_ops = [
                UpdateOne(
                    {
                        "inst_id": record["inst_id"],
                        "bar": record["bar"],
                        "timestamp": record["timestamp"],
                    },
                    {"$set": record},
                    upsert=True,
                )
                for record in data_to_save
            ]
            result = collection.bulk_write(bulk_ops, ordered=False)
            logger.info(
                "Upserted %s feature records, modified %s",
                result.upserted_count,
                result.modified_count,
            )
            return True
        except BulkWriteError as e:
            logger.error(f"Failed to save features (bulk write error): {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to save features: {e}")
            return False
    
    def get_features(self, limit: int = 1000, inst_id: str = None, bar: str = None, isNull: bool = False, regime_null: bool = None, as_model: bool = False) -> Union[List[Dict[str, Any]], List[Feature]]:
        """
        Retrieve feature data.
        
        Args:
            limit: Maximum number of records to retrieve
            inst_id: Instrument ID to filter by
            bar: Time interval to filter by
            isNull: Filter for records with null label
            regime_null: True=仅无 regime_label; False=全部; None=不筛选
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
            
            # 默认查询label非空的记录
            if isNull:
                # 查询label为空的情况：null、空字符串、或字段不存在
                query["$or"] = [
                    {"label": None},
                    {"label": ""},
                    {"label": {"$exists": False}}
                ]
            else:
                # 查询label非空的情况：字段存在且不为null且不为空字符串
                query["$and"] = [
                    {"label": {"$exists": True}},
                    {"label": {"$ne": None}},
                    {"label": {"$ne": ""}}
                ]

            if regime_null is True:
                query["$or"] = [
                    {"regime_label": None},
                    {"regime_label": {"$exists": False}},
                ]
            elif regime_null is False:
                query["regime_label"] = {"$exists": True, "$ne": None}
            
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

    def get_all_features(
        self, inst_id: str = "ETH-USDT-SWAP", bar: str = "1H", limit: int = 50000
    ) -> List[Dict[str, Any]]:
        """获取全部 feature（用于 regime 全量重标注）。"""
        try:
            collection = self._get_collection()
            if collection is None:
                return []
            query = {"inst_id": inst_id, "bar": bar}
            cursor = collection.find(query).sort("timestamp", -1).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to get all features: {e}")
            return []

    def count_features(self, inst_id: str, bar: str = "1H") -> int:
        try:
            collection = self._get_collection()
            if collection is None:
                return 0
            return collection.count_documents({"inst_id": inst_id, "bar": bar})
        except Exception as e:
            logger.error(f"Failed to count features: {e}")
            return 0

    def count_regime_labeled(self, inst_id: str, bar: str = "1H") -> int:
        try:
            collection = self._get_collection()
            if collection is None:
                return 0
            return collection.count_documents({
                "inst_id": inst_id,
                "bar": bar,
                "regime_label": {"$exists": True, "$ne": None},
            })
        except Exception as e:
            logger.error(f"Failed to count regime labels: {e}")
            return 0

    def get_features_without_regime(
        self, inst_id: str = "ETH-USDT-SWAP", bar: str = "1H", limit: int = 50000
    ) -> List[Dict[str, Any]]:
        try:
            collection = self._get_collection()
            if collection is None:
                return []
            query = {
                "inst_id": inst_id,
                "bar": bar,
                "$or": [
                    {"regime_label": None},
                    {"regime_label": {"$exists": False}},
                ],
            }
            cursor = collection.find(query).sort("timestamp", -1).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to get features without regime: {e}")
            return []

    def get_features_for_regime(
        self, inst_id: str = "ETH-USDT-SWAP", bar: str = "1H", limit: int = 10000
    ) -> List[Dict[str, Any]]:
        """获取已标注 regime_label 的特征，按时间正序。"""
        try:
            collection = self._get_collection()
            if collection is None:
                return []
            query = {
                "inst_id": inst_id,
                "bar": bar,
                "regime_label": {"$exists": True, "$ne": None},
            }
            cursor = collection.find(query).sort("timestamp", 1).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to get regime features: {e}")
            return []

    def update_regime_label(
        self, inst_id: str, timestamp: int, regime_label: int, bar: str = "1H"
    ) -> Dict[str, int]:
        try:
            collection = self._get_collection()
            if collection is None:
                return {"matched": 0, "modified": 0}
            result = collection.update_one(
                {"inst_id": inst_id, "timestamp": timestamp, "bar": bar},
                {"$set": {"regime_label": regime_label}},
            )
            return {
                "matched": result.matched_count,
                "modified": result.modified_count,
            }
        except Exception as e:
            logger.error(f"Failed to update regime_label: {e}")
            return {"matched": 0, "modified": 0}

feature_handler = FeatureDataHandler()