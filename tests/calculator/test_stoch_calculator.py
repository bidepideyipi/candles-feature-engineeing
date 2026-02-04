"""
Stochastic Oscillator Unit Tests
Test Stochastic calculation accuracy and edge cases
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from utils.stoch_calculator import STOCH_CALCULATOR


class TestStochasticCalculator:
    """Test suite for StochasticCalculator class"""
    
    def test_stochastic_calculation(self):
        prices = np.linspace(100, 150, 30)
        high = prices + 1
        low = prices - 1
        
        df = pd.DataFrame({'high': high, 'low': low, 'close': prices})
        k, d = STOCH_CALCULATOR.calculate(df)
        assert 0 <= k <= 100, "%K should be between 0 and 100"
        assert 0 <= d <= 100, "%D should be between 0 and 100"
    
    def test_stochastic_overbought(self):
        prices = np.linspace(100, 130, 30)
        high = prices + 5
        low = prices - 2
        
        df = pd.DataFrame({'high': high, 'low': low, 'close': prices})
        k, d = STOCH_CALCULATOR.calculate(df)
        assert k > 50, "%K should indicate overbought condition"
    
    def test_stochastic_oversold(self):
        prices = np.linspace(130, 100, 30)
        high = prices + 2
        low = prices - 5
        
        df = pd.DataFrame({'high': high, 'low': low, 'close': prices})
        k, d = STOCH_CALCULATOR.calculate(df)
        assert k < 50, "%K should indicate oversold condition"
    
    def test_stochastic_flat_market(self):
        prices = np.full(30, 100)
        high = prices + 1
        low = prices - 1
        
        df = pd.DataFrame({'high': high, 'low': low, 'close': prices})
        k, d = STOCH_CALCULATOR.calculate(df)
        assert k > 40 and k < 60, "%K should be near middle in flat market"
    
    def test_insufficient_data(self):
        prices = np.array([100, 101, 102, 103, 104])
        df = pd.DataFrame({'high': prices + 1, 'low': prices - 1, 'close': prices})
        
        with pytest.raises(ValueError):
            STOCH_CALCULATOR.calculate(df)
    
    def test_missing_columns(self):
        df = pd.DataFrame({'open': [100, 101], 'close': [100, 101]})
        with pytest.raises(ValueError):
            STOCH_CALCULATOR.calculate(df)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
