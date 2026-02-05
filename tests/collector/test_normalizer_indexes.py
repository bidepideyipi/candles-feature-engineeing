"""
Test that normalizer collection has proper indexes to prevent duplicate data.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from collect.normalization_handler import normalization_handler

class TestNormalizerIndexes:
    """Test that indexes are created correctly."""
    
    def test_normalizer_indexes_created(self):
        """Verify that unique indexes exist on normalizer collection."""
        collection = normalization_handler._get_collection()
        
        if collection is None:
            print("ERROR: Could not get collection")
            assert False, "Collection is None"
        
        indexes = collection.index_information()
        
        print("\n=== Normalizer Collection Indexes ===")
        for index_name, index_info in indexes.items():
            print(f"\nIndex: {index_name}")
            print(f"  Keys: {index_info.get('key')}")
            print(f"  Unique: {index_info.get('unique', False)}")
        
        # Check for required indexes
        required_indexes = {
            'unique_inst_id_bar_column': False,
            'idx_inst_id': False,
            'idx_bar': False,
            'idx_column': False
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
        
        collection = normalization_handler._get_collection()
        
        # Create test normalization params
        test_data = {
            "inst_id": "TEST-SWAP",
            "bar": "1H",
            "column": "close",
            "mean": 100.0,
            "std": 10.0
        }
        
        # First insert/upsert should succeed
        print("\n=== Testing Duplicate Prevention ===")
        print("Upserting first record...")
        result = normalization_handler.save_normalization_params(
            inst_id=test_data["inst_id"],
            bar=test_data["bar"],
            column=test_data["column"],
            mean=test_data["mean"],
            std=test_data["std"]
        )
        assert result, "First upsert should succeed"
        print("✓ First upsert successful")
        
        # Second upsert with same keys should update (not create duplicate)
        print("\nUpserting duplicate record (should update existing)...")
        result = normalization_handler.save_normalization_params(
            inst_id=test_data["inst_id"],
            bar=test_data["bar"],
            column=test_data["column"],
            mean=200.0,  # Different mean
            std=20.0     # Different std
        )
        assert result, "Second upsert should succeed (update existing)"
        print("✓ Second upsert updated existing record (not duplicate)")
        
        # Verify the values were updated
        params = normalization_handler.get_normalization_params(
            inst_id=test_data["inst_id"],
            bar=test_data["bar"],
            column=test_data["column"]
        )
        assert params is not None, "Should retrieve params"
        assert params["mean"] == 200.0, f"Mean should be updated to 200.0, got {params['mean']}"
        assert params["std"] == 20.0, f"Std should be updated to 20.0, got {params['std']}"
        print(f"✓ Values correctly updated: mean={params['mean']}, std={params['std']}")
        
        # Cleanup
        print("\nCleaning up test data...")
        collection.delete_many({"inst_id": "TEST-SWAP"})
        print("✓ Cleanup complete")


if __name__ == "__main__":
    test = TestNormalizerIndexes()
    
    print("Testing normalizer collection indexes...")
    test.test_normalizer_indexes_created()
    
    print("\n" + "="*50)
    print("Testing duplicate prevention (upsert behavior)...")
    test.test_duplicate_prevention()
    
    print("\n" + "="*50)
    print("✓ All tests passed!")
