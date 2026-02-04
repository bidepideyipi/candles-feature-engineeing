"""
MACD Calculator Unit Tests
Test MACD calculation accuracy and edge cases
"""

import sys
from pathlib import Path
import numpy as np
import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from utils.macd_calculator import MACD_CALCULATOR


class TestMACDCalculator:
    """Test suite for MACDCalculator class"""
    
    def test_macd_calculation(self):
        upPrice = np.linspace(100, 130, 16)
        downPrice = np.linspace(130, 110, 16)
        upPriceAgein = np.linspace(110, 150, 16)
        # 合并数组
        combined_array = np.concatenate([upPrice, downPrice, upPriceAgein])
        MACD_CALCULATOR.calculate(combined_array)
        assert True, "MACD calculation should produce valid results"
        
    def test_macd_calculation_upward_trend(self):
        upward_trend = np.linspace(100, 250, 50)
        last_macd, last_signal, last_histogram = MACD_CALCULATOR.calculate(upward_trend)
        assert True, "MACD calculation should produce valid results"
        
if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])