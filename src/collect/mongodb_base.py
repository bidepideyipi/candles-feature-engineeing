"""
Base MongoDB handler providing common functionality.
"""

import logging
from typing import Optional
from pymongo import MongoClient
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
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Global instances will be created in individual handler files