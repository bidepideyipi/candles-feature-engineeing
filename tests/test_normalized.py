"""
Normalized utility unit tests
Test normalization functions and edge cases
"""

import sys
from pathlib import Path
import numpy as np
import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.normalized import NORMALIZED
import logging
logging.basicConfig(level=logging.DEBUG)

class TestNormalized:
    """Test suite for Normalized class"""
    
    def test_calculate(self):
        """Test the calculate method"""
        # Create test data
        prices = np.linspace(100, 350, 30)
        result = NORMALIZED.calculate(prices)
        assert result < 2.0 and result > 1.0
           
if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])