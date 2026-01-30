"""
Normalized utility unit tests
Test normalization functions and edge cases
"""

import sys
from pathlib import Path
import numpy as np
import pytest
import pandas as pd

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.atr_calculator import ATR
import logging
logging.basicConfig(level=logging.DEBUG)

class TestATR:
    """Test suite for ATR class"""
    
    def test_calculate(self):
        """Test the calculate method"""
        # Create test data
        prices = np.linspace(100, 350, 30)
        high = prices + 1
        low = prices - 1
        
        df = pd.DataFrame({'high': high, 'low': low, 'close': prices})
        result = ATR.calculate(df)
        assert result > 9
           
if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])