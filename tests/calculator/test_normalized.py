"""
Normalized utility unit tests
Test normalization functions and edge cases
"""

import sys
from pathlib import Path
import pandas as pd
import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from utils.normalize_encoder import NORMALIZED
#测试获取数组格式的数据
from collect.mongodb_handler import mongo_handler

import logging
logging.basicConfig(level=logging.DEBUG)

class TestNormalized:
    """Test suite for Normalized class"""
    
    def test_calculate(self):
        """Test the calculate method"""
        # Create test data
        #prices = np.linspace(100, 350, 30)
        
        prices = mongo_handler.get_candlestick_data(inst_id="ETH-USDT-SWAP", bar="1H", limit=200)
        
        # Extract close prices and convert to pandas Series
        close_prices = pd.Series([item['close'] for item in prices])
    
        result = NORMALIZED.calculate(close_prices)
        assert True
           
if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])