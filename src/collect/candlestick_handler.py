"""
Candlestick data handler for MongoDB operations.
Handles candlestick data storage and retrieval.
"""

import logging
from typing import List, Dict, Any, Optional
from pymongo import UpdateOne

from config.settings import config
from .mongodb_base import MongoDBBaseHandler

logger = logging.getLogger(__name__)

class CandlestickDataHandler(MongoDBBaseHandler):
    """Handler for candlestick data operations."""
    
    def __init__(self):
        super().__init__()
        self.collection_name = config.MONGODB_COLLECTIONS['candlesticks']
    
    def save_candlestick_data(self, data: List[Dict[str, Any]]) -> bool:
        """
        Save candlestick data to MongoDB with upsert capability.
        
        Args:
            data: List of candlestick dictionaries
            
        Returns:
            bool: True if save successful, False otherwise
        """
        if not data:
            logger.warning("No candlestick data to save")
            return True
            
        try:
            collection = self._get_collection()
            if collection is None:
                return False
            
            # Batch upsert operation using composite key
            bulk_operations = []
            for record in data:
                bulk_operations.append(
                    UpdateOne(
                        {
                            "inst_id": record["inst_id"],
                            "bar": record["bar"],
                            "timestamp": record["timestamp"]
                        },
                        {"$set": record},
                        upsert=True
                    )
                )
            
            if bulk_operations:
                result = collection.bulk_write(bulk_operations)
                logger.info(f"Upserted {result.upserted_count} new candlestick records, "
                           f"modified {result.modified_count} existing records")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save candlestick data: {e}")
            return False
    
    def get_candlestick_data(self, limit: int = 500, inst_id: str = None, bar: str = None, before: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve candlestick data ordered by timestamp (ascending).
        
        Args:
            limit: Maximum number of records to retrieve
            inst_id: Instrument ID to filter by
            bar: Time interval to filter by
            before: Only retrieve data with timestamp less than this value
            
        Returns:
            List of candlestick data sorted by timestamp
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
            if before:
                query["timestamp"] = {"$lt": before}
            
            cursor = collection.find(query).sort("timestamp", 1).limit(limit)
            return list(cursor)
            
        except Exception as e:
            logger.error(f"Failed to retrieve candlestick data: {e}")
            return []
    
    def get_latest_timestamp(self, inst_id: str = None, bar: str = None) -> Optional[int]:
        """
        Get the latest timestamp from stored candlestick data.
        
        Args:
            inst_id: Instrument ID to filter by
            bar: Time interval to filter by
            
        Returns:
            Latest timestamp or None if no data exists
        """
        try:
            collection = self._get_collection()
            if collection is None:
                return None
            
            # Build query filter
            query = {}
            if inst_id:
                query["inst_id"] = inst_id
            if bar:
                query["bar"] = bar
            
            latest_doc = collection.find_one(
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
            Earliest timestamp or None if no data exists
        """
        try:
            collection = self._get_collection()
            if collection is None:
                return None
            
            # Build query filter
            query = {}
            if inst_id:
                query["inst_id"] = inst_id
            if bar:
                query["bar"] = bar
            
            earliest_doc = collection.find_one(
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
    
    def count(self, inst_id: str, bar: str) -> int:
        """
        Get the total count of candlestick documents matching the criteria.
        
        Args:
            inst_id: Instrument ID to filter by
            bar: Time interval to filter by
            
        Returns:
            Total count of matching documents
        """
        try:
            collection = self._get_collection()
            if collection is None:
                return 0
            
            # Build query filter
            query = {}
            if inst_id:
                query["inst_id"] = inst_id
            if bar:
                query["bar"] = bar
            
            count = collection.count_documents(query)
            return count
            
        except Exception as e:
            logger.error(f"Failed to count candlestick documents: {e}")
            return 0

# Global instance
candlestick_handler = CandlestickDataHandler()