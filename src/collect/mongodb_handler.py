"""
MongoDB connection and data storage utilities.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from ..config.settings import config

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
            self.collection = self.db[config.MONGODB_COLLECTION]
            
            logger.info(f"Connected to MongoDB at {config.MONGODB_URI}")
            logger.info(f"Database: {config.MONGODB_DATABASE}")
            logger.info(f"Collection: {config.MONGODB_COLLECTION}")
            
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def insert_candlestick_data(self, data: List[Dict[str, Any]]) -> bool:
        """
        Insert candlestick data into MongoDB.
        
        Args:
            data: List of candlestick data dictionaries
            
        Returns:
            bool: True if insertion successful, False otherwise
        """
        if self.collection is None:
            logger.error("No MongoDB collection available")
            return False
        
        try:
            if data:
                # Add timestamp for insertion
                for item in data:
                    item['inserted_at'] = datetime.utcnow()
                
                result = self.collection.insert_many(data)
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
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Global instance
mongo_handler = MongoDBHandler()