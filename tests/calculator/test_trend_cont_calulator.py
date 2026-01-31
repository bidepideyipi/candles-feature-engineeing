"""
Normalized utility unit tests
Test normalization functions and edge cases
"""

import sys
from pathlib import Path
import numpy as np
import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from utils.trend_continuation_calulator import TREND_CONTINUATION_CALCULATOR

class TestTrendContinuationCalculator:
    """Test suite for Normalized class"""
    
    def test_calculate(self):
        """Test the calculate method"""
        # Create test data
        prices = np.linspace(100, 350, 30)
        result = TREND_CONTINUATION_CALCULATOR.calculate(prices)
        assert result < 1 and result > -1
           
if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])