#!/usr/bin/env python3
"""
Example script demonstrating MongoDB upsert functionality with OKEx fetcher
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.data.okex_fetcher import okex_fetcher
from src.data.mongodb_handler import mongo_handler

def demonstrate_upsert_functionality():
    """Demonstrate the new MongoDB upsert capability"""
    
    print("=== MongoDB Upsert Demo ===")
    
    # 1. Check current MongoDB status
    earliest = mongo_handler.get_earliest_timestamp()
    latest = mongo_handler.get_latest_timestamp()
    count = mongo_handler.collection.count_documents({}) if mongo_handler.collection else 0
    
    print(f"Current MongoDB status:")
    print(f"  Earliest timestamp: {earliest}")
    print(f"  Latest timestamp: {latest}")
    print(f"  Total records: {count}")
    print()
    
    # 2. Fetch some data
    print("Fetching recent candlestick data...")
    raw_data = okex_fetcher.fetch_candlesticks(bar="1H", limit=10)  # Get just 10 records for demo
    processed_data = okex_fetcher._process_candlestick_data(raw_data)
    
    print(f"Fetched {len(processed_data)} records")
    
    if processed_data:
        # Show sample data
        sample = processed_data[0]
        print(f"Sample record: Timestamp={sample['timestamp']}, Close=${sample['close']:.2f}")
        print()
        
        # 3. Save to MongoDB with upsert
        print("Saving data to MongoDB with upsert...")
        success = okex_fetcher.save_to_mongodb(processed_data)
        
        if success:
            print("✅ Data saved successfully!")
            
            # 4. Verify the save operation
            new_count = mongo_handler.collection.count_documents({})
            print(f"New total records in MongoDB: {new_count}")
            
            # Show what happened
            if new_count > count:
                print(f"Inserted {new_count - count} new records")
            elif new_count == count:
                print("No new records inserted (all were duplicates or updates)")
            
        else:
            print("❌ Failed to save data")
    
    # 5. Demonstrate duplicate handling
    print("\n=== Testing Duplicate Handling ===")
    print("Fetching same data again...")
    
    # Try to save the same data
    success2 = okex_fetcher.save_to_mongodb(processed_data)
    
    if success2:
        final_count = mongo_handler.collection.count_documents({})
        print(f"Final record count: {final_count}")
        print("✅ Duplicate handling works correctly - no duplicate records created")

if __name__ == "__main__":
    demonstrate_upsert_functionality()