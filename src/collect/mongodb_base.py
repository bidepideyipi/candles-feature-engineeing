"""
Base MongoDB handler providing common functionality.
"""

import logging
from typing import Optional, List, Union, Tuple
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from config.settings import config

logger = logging.getLogger(__name__)

class MongoDBBaseHandler:
    """Base class for MongoDB handlers providing common database operations."""
    
    def __init__(self):
        """Initialize MongoDB connection."""
        self.client: Optional[MongoClient] = None
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
            self.client = MongoClient(
                config.MONGODB_URI,
                serverSelectionTimeoutMS=5000
            )
            # Test the connection
            self.client.admin.command('ping')
            
            self.db = self.client[config.MONGODB_DATABASE]
            logger.info(f"Connected to MongoDB at {config.MONGODB_URI}")
            logger.info(f"Database: {config.MONGODB_DATABASE}")
            
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def _get_collection(self):
        """
        Get the collection for this handler.
        
        Returns:
            Collection object or None if not available
        """
        if self.db is None or self.collection_name is None:
            return None
        return self.db[self.collection_name]
    
    def _create_indexes(self, indexes: List[Tuple[Union[str, Tuple[str, ...]], bool]]):
        """
        Create indexes for the collection.
        
        Args:
            indexes: List of tuples (field_spec, is_unique):
                - Single field: ('field_name', is_unique)
                - Composite: (('field1', 'field2', ...), is_unique)
        """
        try:
            collection = self._get_collection()
            if collection is None:
                return
            
            existing_indexes = collection.index_information()
            
            for field_spec, is_unique in indexes:
                if isinstance(field_spec, str):
                    field_names = (field_spec,)
                else:
                    field_names = field_spec
                
                # Generate index key and name
                index_key = "_".join(f"{f}_1" for f in field_names)
                index_name = f"unique_{'_'.join(field_names)}" if is_unique else f"idx_{'_'.join(field_names)}"
                index_keys = [(f, ASCENDING) for f in field_names]
                
                # Skip if index already exists
                if index_key in existing_indexes:
                    logger.info(f"Index '{index_name}' already exists, skipping")
                    continue
                
                if is_unique:
                    # Remove duplicate documents before creating unique index
                    logger.info(f"Cleaning up duplicates for fields {list(field_names)}")
                    self._remove_duplicates(collection, list(field_names))
                    
                    collection.create_index(
                        index_keys,
                        name=index_name,
                        unique=True,
                        background=True
                    )
                    logger.info(f"Created unique index: {index_name} on fields {list(field_names)}")
                else:
                    collection.create_index(
                        index_keys,
                        name=index_name,
                        background=True
                    )
                    logger.info(f"Created index: {index_name} on fields {list(field_names)}")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    def _remove_duplicates(self, collection, unique_fields):
        """
        Remove duplicate documents based on unique fields.
        
        Args:
            collection: MongoDB collection
            unique_fields: List of field names that define uniqueness
        """
        try:
            # Use aggregation to find duplicates
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
            
            duplicates = list(collection.aggregate(pipeline))
            
            if not duplicates:
                logger.info(f"No duplicates found for fields {unique_fields}")
                return
            
            total_removed = 0
            for duplicate_group in duplicates:
                # Keep the first one, delete the rest
                ids_to_delete = duplicate_group["ids"][1:]  # Keep first, delete rest
                if ids_to_delete:
                    result = collection.delete_many({"_id": {"$in": ids_to_delete}})
                    total_removed += result.deleted_count
                    logger.info(f"Removed {result.deleted_count} duplicates for {duplicate_group['_id']}")
            
            logger.info(f"Total duplicates removed: {total_removed}")
            
        except Exception as e:
            logger.error(f"Failed to remove duplicates: {e}")
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Global instances will be created in individual handler files