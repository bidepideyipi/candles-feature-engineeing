"""
Async Candlestick data handler for MongoDB operations.
Handles candlestick data storage and retrieval.
"""

import logging
from typing import List, Dict, Any, Optional
from pymongo import UpdateOne

from config.settings import config
from .mongodb_async_base import AsyncMongoDBBaseHandler

logger = logging.getLogger(__name__)

class AsyncCandlestickDataHandler(AsyncMongoDBBaseHandler):
    """Async handler for candlestick data operations."""
    
    def __init__(self):
        super().__init__()
        self.collection_name = config.MONGODB_COLLECTIONS['candlesticks']
    
    async def save_candlestick_data(self, data: List[Dict[str, Any]]) -> bool:
        """
        Save candlestick data to MongoDB with upsert capability (async).
        
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
                result = await collection.bulk_write(bulk_operations)
                logger.info(f"Upserted {result.upserted_count} new candlestick records, "
                           f"modified {result.modified_count} existing records")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save candlestick data: {e}")
            return False
    
    async def get_candlestick_data(self, limit: int = 500, inst_id: str = None, bar: str = None, before: Optional[int] = None, after: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve candlestick data ordered by timestamp (async).
        
        Args:
            limit: Maximum number of records to retrieve
            inst_id: Instrument ID to filter by
            bar: Time interval to filter by
            before: Only retrieve data with timestamp less than this value
            after: Only retrieve data with timestamp greater than this value
            
        Returns:
            List of candlestick data sorted by timestamp
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
                
            if before:
                query["timestamp"] = {"$lt": before}
                cursor = collection.find(query).sort("timestamp", -1).limit(limit)
            elif after:
                query["timestamp"] = {"$gt": after}
                cursor = collection.find(query).sort("timestamp", 1).limit(limit)
            else:
                cursor = collection.find(query).sort("timestamp", 1).limit(limit)
            
            result = []
            async for doc in cursor:
                result.append(doc)
            return result
            
        except Exception as e:
            logger.error(f"Failed to retrieve candlestick data: {e}")
            return []
    
    async def get_latest_timestamp(self, inst_id: str = None, bar: str = None) -> Optional[int]:
        """
        Get the latest timestamp from stored candlestick data (async).
        
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
            
            query = {}
            if inst_id:
                query["inst_id"] = inst_id
            if bar:
                query["bar"] = bar
            
            latest_doc = await collection.find_one(
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
    
    async def get_earliest_timestamp(self, inst_id: str = None, bar: str = None) -> Optional[int]:
        """
        Get the earliest timestamp from stored candlestick data (async).
        
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
            
            query = {}
            if inst_id:
                query["inst_id"] = inst_id
            if bar:
                query["bar"] = bar
            
            earliest_doc = await collection.find_one(
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
    
    async def count(self, inst_id: str, bar: str) -> int:
        """
        Get the total count of candlestick documents matching criteria (async).
        
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
            
            query = {}
            if inst_id:
                query["inst_id"] = inst_id
            if bar:
                query["bar"] = bar
            
            count = await collection.count_documents(query)
            return count
            
        except Exception as e:
            logger.error(f"Failed to count candlestick documents: {e}")
            return 0

# Global instance
async_candlestick_handler = AsyncCandlestickDataHandler()
