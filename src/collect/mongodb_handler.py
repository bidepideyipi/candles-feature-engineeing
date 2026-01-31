"""
MongoDB connection and data storage utilities.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from config.settings import config

logger = logging.getLogger(__name__)

class MongoDBHandler:
    """Handles MongoDB connection and data operations."""
    
    def __init__(self):
        """Initialize MongoDB connection."""
        self.client: Optional[MongoClient] = None
        self.db = None
        self.collection = None
        self.connect()
    
    def connect(self) -> bool:
        """
        Establish connection to MongoDB.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = MongoClient(
                config.MONGODB_URI,
                serverSelectionTimeoutMS=5000
            )
            # Test the connection
            self.client.admin.command('ping')
            
            self.db = self.client[config.MONGODB_DATABASE]
            # Initialize collections
            self.collections = {
                'candlesticks': self.db[config.MONGODB_COLLECTIONS['candlesticks']],
                'features': self.db[config.MONGODB_COLLECTIONS['features']],
                'normalizer': self.db[config.MONGODB_COLLECTIONS['normalizer']]
            }
            # Default collection for backward compatibility
            self.collection = self.collections['candlesticks']
            
            logger.info(f"Connected to MongoDB at {config.MONGODB_URI}")
            logger.info(f"Database: {config.MONGODB_DATABASE}")
            logger.info(f"Collections: {config.MONGODB_COLLECTIONS}")
            
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def _get_collection(self, collection_name: str = 'candlesticks'):
        """Get collection by name"""
        return self.collections.get(collection_name, self.collection)
    
    def insert_candlestick_data(self, data: List[Dict[str, Any]]) -> bool:
        """
        Insert candlestick data into MongoDB.
        
        Args:
            data: List of candlestick data dictionaries
            
        Returns:
            bool: True if insertion successful, False otherwise
        """
        collection = self._get_collection('candlesticks')
        if collection is None:
            logger.error("No MongoDB collection available")
            return False
        
        try:
            if data:
                # Add timestamp for insertion
                for item in data:
                    item['inserted_at'] = datetime.utcnow()
                
                result = collection.insert_many(data)
                logger.info(f"Inserted {len(result.inserted_ids)} candlestick records")
                return True
            else:
                logger.warning("No data to insert")
                return False
                
        except Exception as e:
            logger.error(f"Failed to insert candlestick data: {e}")
            return False
    
    def get_latest_timestamp(self, inst_id: str = None, bar: str = None) -> Optional[int]:
        """
        Get the latest timestamp from stored candlestick data.
        
        Args:
            inst_id: Instrument ID to filter by
            bar: Time interval to filter by
            
        Returns:
            Optional[int]: Latest timestamp or None if no data exists
        """
        if self.collection is None:
            return None
        
        try:
            # Build query filter
            query = {}
            if inst_id:
                query["inst_id"] = inst_id
            if bar:
                query["bar"] = bar
            
            latest_doc = self.collection.find_one(
                query,
                sort=[("timestamp", -1)],
                projection={"timestamp": 1}
            )
            
            if latest_doc:
                return latest_doc.get("timestamp")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get latest timestamp: {e}")
            return None
    
    def get_earliest_timestamp(self, inst_id: str = None, bar: str = None) -> Optional[int]:
        """
        Get the earliest timestamp from stored candlestick data.
        
        Args:
            inst_id: Instrument ID to filter by
            bar: Time interval to filter by
            
        Returns:
            Optional[int]: Earliest timestamp or None if no data exists
        """
        if self.collection is None:
            return None
        
        try:
            # Build query filter
            query = {}
            if inst_id:
                query["inst_id"] = inst_id
            if bar:
                query["bar"] = bar
            
            earliest_doc = self.collection.find_one(
                query,
                sort=[("timestamp", 1)],
                projection={"timestamp": 1}
            )
            
            if earliest_doc:
                return earliest_doc.get("timestamp")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get earliest timestamp: {e}")
            return None
    
    #从数据库取出数据
    def get_candlestick_data(self, limit: int = 500, inst_id: str = None, bar: str = None) -> List[Dict[str, Any]]:
        """
        Retrieve candlestick data ordered by timestamp (ascending).
        
        Args:
            limit: Maximum number of records to retrieve
            inst_id: Instrument ID to filter by (e.g., "ETH-USDT-SWAP")
            bar: Time interval to filter by
            
        Returns:
            List[Dict[str, Any]]: Candlestick data sorted by timestamp
        """
        if self.collection is None:
            return []
        
        try:
            # Build query filter
            query = {}
            if inst_id:
                query["inst_id"] = inst_id
            if bar:
                query["bar"] = bar
            
            cursor = self.collection.find(query).sort("timestamp", 1).limit(limit)
            return list(cursor)
            
        except Exception as e:
            logger.error(f"Failed to retrieve candlestick data: {e}")
            return []
    
    def save_features(self, features_data: List[Dict[str, Any]]) -> bool:
        """
        Save calculated features to MongoDB features collection.
        
        Args:
            features_data: List of feature dictionaries
            
        Returns:
            bool: True if save successful, False otherwise
        """
        collection = self._get_collection('features')
        if collection is None:
            logger.error("No features collection available")
            return False
        
        try:
            if features_data:
                result = collection.insert_many(features_data)
                logger.info(f"Saved {len(result.inserted_ids)} feature records")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to save features: {e}")
            return False
    
    def save_normalization_params(self, inst_id: str, bar: str, mean: float, std: float) -> bool:
        """
        Save normalization parameters to MongoDB normalizer collection.
        
        Args:
            inst_id: Instrument ID
            bar: Time interval
            mean: Training data mean
            std: Training data standard deviation
            
        Returns:
            bool: True if save successful, False otherwise
        """
        collection = self._get_collection('normalizer')
        if collection is None:
            logger.error("No normalizer collection available")
            return False
        
        try:
            # Upsert operation - update if exists, insert if not
            result = collection.update_one(
                {"inst_id": inst_id, "bar": bar},
                {
                    "$set": {
                        "mean": mean,
                        "std": std,
                        "updated_at": datetime.utcnow()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            logger.info(f"Saved normalization params for {inst_id} {bar}")
            return True
        except Exception as e:
            logger.error(f"Failed to save normalization params: {e}")
            return False
    
    def get_normalization_params(self, inst_id: str, bar: str) -> Optional[Dict[str, float]]:
        """
        Retrieve normalization parameters from MongoDB.
        
        Args:
            inst_id: Instrument ID
            bar: Time interval
            
        Returns:
            Dict with 'mean' and 'std' keys, or None if not found
        """
        collection = self._get_collection('normalizer')
        if collection is None:
            return None
        
        try:
            doc = collection.find_one({"inst_id": inst_id, "bar": bar})
            if doc:
                return {"mean": doc["mean"], "std": doc["std"]}
            return None
        except Exception as e:
            logger.error(f"Failed to get normalization params: {e}")
            return None
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Global instance
mongo_handler = MongoDBHandler()