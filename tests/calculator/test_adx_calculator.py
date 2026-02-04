"""
ADX Calculator Unit Tests
Test ADX calculation accuracy and edge cases
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from utils.adx_calculator import ADX_CALCULATOR


class TestADXCalculator:
    """Test suite for ADXCalculator class"""
    
    def test_adx_calculation(self):
        prices = np.linspace(100, 150, 30)
        high = prices + np.random.uniform(0, 5, 30)
        low = prices - np.random.uniform(0, 5, 30)
        
        df = pd.DataFrame({'high': high, 'low': low, 'close': prices})
        adx, plus_di, minus_di = ADX_CALCULATOR.calculate(df)
        assert 0 <= adx <= 100, "ADX should be between 0 and 100"
        assert 0 <= plus_di <= 100, "+DI should be between 0 and 100"
        assert 0 <= minus_di <= 100, "-DI should be between 0 and 100"
    
    def test_adx_strong_trend(self):
        prices = np.linspace(100, 200, 50)
        high = prices + 2
        low = prices - 1
        
        df = pd.DataFrame({'high': high, 'low': low, 'close': prices})
        adx, plus_di, minus_di = ADX_CALCULATOR.calculate(df)
        assert adx > 30, "ADX should indicate strong trend"
    
    def test_adx_weak_trend(self):
        prices = np.random.uniform(100, 102, 50)
        high = prices + 1
        low = prices - 1
        
        df = pd.DataFrame({'high': high, 'low': low, 'close': prices})
        adx, plus_di, minus_di = ADX_CALCULATOR.calculate(df)
        assert adx < 25, "ADX should indicate weak trend/no trend"
    
    def test_adx_upward_trend(self):
        prices = np.linspace(100, 150, 40)
        high = prices + 1
        low = prices - 1
        
        df = pd.DataFrame({'high': high, 'low': low, 'close': prices})
        adx, plus_di, minus_di = ADX_CALCULATOR.calculate(df)
        assert plus_di > minus_di, "+DI should be greater than -DI in uptrend"
    
    def test_adx_downward_trend(self):
        prices = np.linspace(150, 100, 40)
        high = prices + 1
        low = prices - 1
        
        df = pd.DataFrame({'high': high, 'low': low, 'close': prices})
        adx, plus_di, minus_di = ADX_CALCULATOR.calculate(df)
        assert minus_di > plus_di, "-DI should be greater than +DI in downtrend"
    
    def test_insufficient_data(self):
        prices = np.linspace(100, 120, 20)
        df = pd.DataFrame({'high': prices + 1, 'low': prices - 1, 'close': prices})
        
        with pytest.raises(ValueError):
            ADX_CALCULATOR.calculate(df)
    
    def test_missing_columns(self):
        df = pd.DataFrame({'open': [100, 101], 'close': [100, 101]})
        with pytest.raises(ValueError):
            ADX_CALCULATOR.calculate(df)
    
    def test_adx_range_validation(self):
        prices = np.linspace(100, 200, 50)
        high = prices + 2
        low = prices - 2
        
        df = pd.DataFrame({'high': high, 'low': low, 'close': prices})
        adx, plus_di, minus_di = ADX_CALCULATOR.calculate(df)
        
        total_di = plus_di + minus_di
        if total_di > 0:
            expected_dx = 100 * abs(plus_di - minus_di) / total_di
            assert adx <= expected_dx + 5, "ADX should be close to smoothed DX"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
