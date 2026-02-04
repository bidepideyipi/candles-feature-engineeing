"""
EMA Calculator Unit Tests
Test EMA calculation accuracy and edge cases
"""

import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from utils.ema_calculator import EMA_12, EMA_26, EMA_50


class TestEMACalculator:
    """Test suite for EMACalculator class"""
    
    def test_ema_calculation(self):
        prices = np.array([100, 101, 102, 103, 104, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94])
        result = EMA_12.calculate(prices)
        assert result > 95 and result < 105, "EMA should be within price range"
    
    def test_ema_calculation_upward_trend(self):
        upward_trend = np.linspace(100, 150, 30)
        result = EMA_12.calculate(upward_trend)
        assert result > 120, "EMA should reflect upward trend"
        
    def test_ema_calculation_downward_trend(self):
        downward_trend = np.linspace(150, 100, 30)
        result = EMA_12.calculate(downward_trend)
        assert result < 130, "EMA should reflect downward trend"
    
    def test_ema_26_period(self):
        prices = np.linspace(100, 200, 30)
        result = EMA_26.calculate(prices)
        assert result > 100 and result < 200, "EMA 26 should be within price range"
    
    def test_ema_50_period(self):
        prices = np.linspace(100, 200, 60)
        result = EMA_50.calculate(prices)
        assert result > 100 and result < 200, "EMA 50 should be within price range"
    
    def test_insufficient_data(self):
        with pytest.raises(ValueError):
            EMA_12.calculate(np.array([100, 101, 102]))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
