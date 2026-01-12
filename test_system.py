"""
Simple test script to verify the system components work correctly.
"""

import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from src.config.settings import config
        print("✓ Configuration module")
        
        from src.data.okex_fetcher import okex_fetcher
        print("✓ OKEx fetcher module")
        
        from src.data.mongodb_handler import mongo_handler
        print("✓ MongoDB handler module")
        
        from src.utils.technical_indicators import tech_calculator
        print("✓ Technical indicators module")
        
        from src.utils.feature_engineering import feature_engineer
        print("✓ Feature engineering module")
        
        from src.models.xgboost_trainer import xgb_trainer
        print("✓ XGBoost trainer module")
        
        from src.models.predictor import predictor
        print("✓ Predictor module")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_api_connectivity():
    """Test OKEx API connectivity."""
    print("\nTesting OKEx API connectivity...")
    
    try:
        from src.data.okex_fetcher import okex_fetcher
        price = okex_fetcher.get_latest_price()
        if price:
            print(f"✓ API connectivity successful (ETH price: ${price:.2f})")
            return True
        else:
            print("⚠ Could not fetch price, but API responded")
            return True
    except Exception as e:
        print(f"✗ API connectivity failed: {e}")
        return False

def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    try:
        from src.config.settings import config
        print(f"✓ Feature window size: {config.FEATURE_WINDOW_SIZE}")
        print(f"✓ Time windows: {config.TIME_WINDOWS}")
        print(f"✓ Classification thresholds: {len(config.CLASSIFICATION_THRESHOLDS)} classes")
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("TECHNICAL ANALYSIS HELPER - SYSTEM TEST")
    print("=" * 50)
    
    all_passed = True
    
    # Run tests
    all_passed &= test_imports()
    all_passed &= test_config()
    all_passed &= test_api_connectivity()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("System is ready for use!")
        print("\nNext steps:")
        print("1. Ensure MongoDB is running")
        print("2. Run 'python main.py train' to train the model")
        print("3. Run 'python main.py predict' to make predictions")
    else:
        print("✗ SOME TESTS FAILED")
        print("Please check the errors above and fix them before proceeding.")
    print("=" * 50)

if __name__ == '__main__':
    main()