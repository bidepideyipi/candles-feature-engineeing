#!/usr/bin/env python3
"""
Debug script to test MongoDB connection and collection access
"""

import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.data.mongodb_handler import mongo_handler
    print("✓ MongoDB handler imported successfully")
    
    # Test connection
    connected = mongo_handler.connect()
    print(f"✓ MongoDB connection: {'Success' if connected else 'Failed'}")
    
    # Test collection access
    if mongo_handler.collection is not None:
        print("✓ Collection object exists")
        print(f"Collection name: {mongo_handler.collection.name}")
    else:
        print("✗ Collection is None")
    
    # Test basic operations
    try:
        earliest = mongo_handler.get_earliest_timestamp()
        latest = mongo_handler.get_latest_timestamp()
        print(f"Earliest timestamp: {earliest}")
        print(f"Latest timestamp: {latest}")
        
        data = mongo_handler.get_candlestick_data(limit=5)
        print(f"Retrieved {len(data)} records")
        
    except Exception as e:
        print(f"✗ Error in MongoDB operations: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()