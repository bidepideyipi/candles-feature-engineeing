"""
Async Base MongoDB handler providing common functionality.
"""

import logging
from typing import Optional, List, Union, Tuple
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
from pymongo.errors import ConnectionFailure

from config.settings import config

logger = logging.getLogger(__name__)

class AsyncMongoDBBaseHandler:
    """Async base class for MongoDB handlers providing common database operations."""
    
    def __init__(self):
        """Initialize async MongoDB connection."""
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.collection_name = None
        self._connect()
    
    def _connect(self) -> bool:
        """
        Establish connection to MongoDB.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = AsyncIOMotorClient(
                config.MONGODB_URI,
                serverSelectionTimeoutMS=5000
            )
            self.db = self.client[config.MONGODB_DATABASE]
            logger.info(f"Connected to MongoDB (async) at {config.MONGODB_URI}")
            logger.info(f"Database: {config.MONGODB_DATABASE}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB (async): {e}")
            return False
    
    def _get_collection(self):
        """
        Get collection for this handler.
        
        Returns:
            Collection object or None if not available
        """
        if self.db is None or self.collection_name is None:
            return None
        return self.db[self.collection_name]
    
    async def _create_indexes(self, indexes: List[Tuple[Union[str, Tuple[str, ...]], bool]]):
        """
        Create indexes for collection (async).
        
        Args:
            indexes: List of tuples (field_spec, is_unique):
                - Single field: ('field_name', is_unique)
                - Composite: (('field1', 'field2', ...), is_unique)
        """
        try:
            collection = self._get_collection()
            if collection is None:
                return
            
            existing_indexes = await collection.index_information()
            
            for field_spec, is_unique in indexes:
                if isinstance(field_spec, str):
                    field_names = (field_spec,)
                else:
                    field_names = field_spec
                
                index_key = "_".join(f"{f}_1" for f in field_names)
                index_name = f"unique_{'_'.join(field_names)}" if is_unique else f"idx_{'_'.join(field_names)}"
                index_keys = [(f, ASCENDING) for f in field_names]
                
                if index_key in existing_indexes:
                    logger.info(f"Index '{index_name}' already exists, skipping")
                    continue
                
                if is_unique:
                    await self._remove_duplicates(collection, list(field_names))
                    
                    await collection.create_index(
                        index_keys,
                        name=index_name,
                        unique=True,
                        background=True
                    )
                    logger.info(f"Created unique index: {index_name} on fields {list(field_names)}")
                else:
                    await collection.create_index(
                        index_keys,
                        name=index_name,
                        background=True
                    )
                    logger.info(f"Created index: {index_name} on fields {list(field_names)}")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    async def _remove_duplicates(self, collection, unique_fields):
        """
        Remove duplicate documents based on unique fields (async).
        
        Args:
            collection: MongoDB collection
            unique_fields: List of field names that define uniqueness
        """
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": {field: f"${field}" for field in unique_fields},
                        "count": {"$sum": 1},
                        "ids": {"$push": "$_id"}
                    }
                },
                {
                    "$match": {"count": {"$gt": 1}}
                },
                {
                    "$sort": {"count": -1}
                }
            ]
            
            duplicates = []
            async for doc in collection.aggregate(pipeline):
                duplicates.append(doc)
            
            if not duplicates:
                logger.info(f"No duplicates found for fields {unique_fields}")
                return
            
            total_removed = 0
            for duplicate_group in duplicates:
                ids_to_delete = duplicate_group["ids"][1:]
                if ids_to_delete:
                    result = await collection.delete_many({"_id": {"$in": ids_to_delete}})
                    total_removed += result.deleted_count
                    logger.info(f"Removed {result.deleted_count} duplicates for {duplicate_group['_id']}")
            
            logger.info(f"Total duplicates removed: {total_removed}")
            
        except Exception as e:
            logger.error(f"Failed to remove duplicates: {e}")
    
    async def close(self):
        """Close MongoDB connection (async)."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed (async)")
