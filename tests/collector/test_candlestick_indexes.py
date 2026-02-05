"""
Test that candlesticks collection has proper indexes to prevent duplicate data.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from collect.candlestick_handler import candlestick_handler

class TestCandlestickIndexes:
    """Test that indexes are created correctly."""
    
    def test_candlestick_indexes_created(self):
        """Verify that unique indexes exist on candlesticks collection."""
        collection = candlestick_handler._get_collection()
        
        if collection is None:
            print("ERROR: Could not get collection")
            assert False, "Collection is None"
        
        indexes = collection.index_information()
        
        print("\n=== Candlesticks Collection Indexes ===")
        for index_name, index_info in indexes.items():
            print(f"\nIndex: {index_name}")
            print(f"  Keys: {index_info.get('key')}")
            print(f"  Unique: {index_info.get('unique', False)}")
        
        # Check for required indexes
        required_indexes = {
            'unique_inst_id_timestamp_bar': False,
            'idx_timestamp': False,
            'idx_inst_id': False,
            'idx_bar': False
        }
        
        for index_name in indexes.keys():
            for required in required_indexes:
                if required in index_name:
                    required_indexes[required] = True
        
        print("\n=== Required Indexes Status ===")
        all_present = True
        for index_name, present in required_indexes.items():
            status = "✓" if present else "✗"
            print(f"{status} {index_name}: {'Present' if present else 'MISSING'}")
            if not present:
                all_present = False
        
        assert all_present, "Some required indexes are missing"
        print("\n✓ All required indexes are present")
    
    def test_duplicate_prevention(self):
        """Test that duplicate data is prevented by unique index."""
        
        collection = candlestick_handler._get_collection()
        
        # Create test candlestick data
        test_data = {
            "timestamp": 1234567890,
            "inst_id": "TEST-SWAP",
            "bar": "1H",
            "open": 100.0,
            "high": 105.0,
            "low": 95.0,
            "close": 103.0,
            "volume": 1000.0,
            "volume_ccy": "USDT",
            "volume_ccy_quote": "ETH",
            "confirm": "1"
        }
        
        # First insert should succeed
        print("\n=== Testing Duplicate Prevention ===")
        print("Inserting first record...")
        try:
            result = collection.insert_one(test_data)
            print(f"✓ First insert successful: {result.inserted_id}")
        except Exception as e:
            print(f"✗ First insert failed: {e}")
            assert False, "First insert should succeed"
        
        # Second insert with same keys should fail (duplicate)
        print("\nInserting duplicate record...")
        try:
            result = collection.insert_one(test_data)
            print(f"✗ Duplicate insert succeeded (should have failed): {result.inserted_id}")
            assert False, "Duplicate insert should fail"
        except Exception as e:
            if 'duplicate' in str(e).lower() or 'duplicate key' in str(e).lower():
                print(f"✓ Duplicate insert correctly prevented: {type(e).__name__}")
            else:
                print(f"✗ Unexpected error: {e}")
                assert False, "Expected duplicate key error"
        
        # Cleanup
        print("\nCleaning up test data...")
        collection.delete_many({"inst_id": "TEST-SWAP"})
        print("✓ Cleanup complete")


if __name__ == "__main__":
    test = TestCandlestickIndexes()
    
    print("Testing candlesticks collection indexes...")
    test.test_candlestick_indexes_created()
    
    print("\n" + "="*50)
    print("Testing duplicate prevention...")
    test.test_duplicate_prevention()
    
    print("\n" + "="*50)
    print("✓ All tests passed!")
