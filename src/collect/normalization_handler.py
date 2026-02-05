"""
Normalization data handler for MongoDB operations.
Handles normalization parameter storage and retrieval.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from config.settings import config
from .mongodb_base import MongoDBBaseHandler

logger = logging.getLogger(__name__)

class NormalizationDataHandler(MongoDBBaseHandler):
    """Handler for normalization parameter operations."""
    
    def __init__(self):
        super().__init__()
        self.collection_name = config.MONGODB_COLLECTIONS['normalizer']
        self._create_indexes([
            ('inst_id', False),
            ('bar', False),
            ('column', False),
            (('inst_id', 'bar', 'column'), True)
        ])
    
    def save_normalization_params(self, inst_id: str, bar: str, column: str, mean: float, std: float) -> bool:
        """
        Save normalization parameters to MongoDB normalizer collection.
        
        Args:
            inst_id: Instrument ID
            bar: Time interval
            column: Column identifier (e.g., "close", "volume", "rsi_14_1h")
            mean: Training data mean
            std: Training data standard deviation
            
        Returns:
            bool: True if save successful, False otherwise
        """
        try:
            collection = self._get_collection()
            if collection is None:
                return False
            
            # Upsert operation - update if exists, insert if not
            result = collection.update_one(
                {"inst_id": inst_id, "bar": bar, "column": column},
                {
                    "$set": {
                        "mean": mean,
                        "column": column,
                        "std": std,
                        "updated_at": datetime.utcnow()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            logger.info(f"Saved normalization params for {inst_id} {bar} {column}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save normalization params: {e}")
            return False
    
    def get_normalization_params(self, inst_id: str, bar: str, column: str) -> Optional[Dict[str, float]]:
        """
        Retrieve normalization parameters from MongoDB.
        
        Args:
            inst_id: Instrument ID
            bar: Time interval
            column: Column identifier
            
        Returns:
            Dict with 'mean' and 'std' keys, or None if not found
        """
        try:
            collection = self._get_collection()
            if collection is None:
                return None
            
            doc = collection.find_one({"inst_id": inst_id, "bar": bar, "column": column})
            if doc:
                return {"mean": doc["mean"], "std": doc["std"]}
            return None
            
        except Exception as e:
            logger.error(f"Failed to get normalization params: {e}")
            return None
    
    def get_all_normalization_params(self) -> List[Dict[str, Any]]:
        """
        Retrieve all normalization parameters.
        
        Returns:
            List of all normalization parameter documents
        """
        try:
            collection = self._get_collection()
            if collection is None:
                return []
            
            cursor = collection.find({})
            return list(cursor)
            
        except Exception as e:
            logger.error(f"Failed to get all normalization params: {e}")
            return []

# Global instance
normalization_handler = NormalizationDataHandler()