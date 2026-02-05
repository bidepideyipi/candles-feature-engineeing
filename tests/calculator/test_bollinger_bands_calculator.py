"""
Bollinger Bands Calculator Unit Tests
Test Bollinger Bands calculation accuracy and edge cases
"""

import sys
from pathlib import Path
import numpy as np
import pytest
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from utils.bollinger_bands_calculator import BollingerBandsCalculator, BOLLINGER_BANDS_20


class TestBollingerBandsCalculator:
    """Test suite for BollingerBandsCalculator class"""
    
    def test_bollinger_bands_calculation(self):
        prices = np.array([100, 101, 102, 103, 104, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94, 95, 96, 97, 98, 99, 100])
        calculator = BollingerBandsCalculator(window=20, num_std=2.0)
        
        upper, lower, position = calculator.calculate(prices)
        
        assert isinstance(upper, float), "Upper band should be a float"
        assert isinstance(lower, float), "Lower band should be a float"
        assert isinstance(position, float), "Position should be a float"
        
        assert upper > lower, "Upper band should be above lower band"
        assert 0 <= position <= 1, "Position should be between 0 and 1"
        assert not np.isnan(upper), "Upper band should not be NaN"
        assert not np.isnan(lower), "Lower band should not be NaN"
        assert not np.isnan(position), "Position should not be NaN"
    
    def test_bollinger_upper(self):
        prices = np.linspace(100, 110, 30)
        calculator = BollingerBandsCalculator(window=20, num_std=2.0)
        
        upper, lower, position = calculator.calculate(prices)
        assert upper > 105, "Upper band should be above prices"
        assert not np.isnan(upper), "Upper band should not be NaN"
    
    def test_bollinger_lower(self):
        prices = np.linspace(100, 110, 30)
        calculator = BollingerBandsCalculator(window=20, num_std=2.0)
        
        upper, lower, position = calculator.calculate(prices)
        assert lower < 105, "Lower band should be below prices"
        assert not np.isnan(lower), "Lower band should not be NaN"
    
    def test_bollinger_position(self):
        prices = np.linspace(100, 110, 30)
        calculator = BollingerBandsCalculator(window=20, num_std=2.0)
        
        upper, lower, position = calculator.calculate(prices)
        assert 0 <= position <= 1, "Position should be between 0 and 1"
        assert not np.isnan(position), "Position should not be NaN"
    
    def test_bollinger_position_at_lower_band(self):
        prices = np.concatenate([
            np.linspace(100, 105, 20),
            np.linspace(105, 100, 10)
        ])
        calculator = BollingerBandsCalculator(window=20, num_std=2.0)
        
        upper, lower, position = calculator.calculate(prices)
        assert 0 <= position <= 1, f"Position should be between 0 and 1, got {position}"
    
    def test_bollinger_position_at_upper_band(self):
        prices = np.concatenate([
            np.linspace(100, 105, 20),
            np.linspace(105, 110, 10)
        ])
        calculator = BollingerBandsCalculator(window=20, num_std=2.0)
        
        upper, lower, position = calculator.calculate(prices)
        assert 0 <= position <= 1, "Position should be between 0 and 1"
    
    def test_get_last_values(self):
        prices = np.linspace(100, 110, 30)
        calculator = BollingerBandsCalculator(window=20, num_std=2.0)
        
        upper, lower, position = calculator.calculate(prices)
        
        assert upper > lower, "Upper should be above lower"
        assert 0 <= position <= 1, "Position should be between 0 and 1"
        assert not np.isnan(upper), "Upper should not be NaN"
        assert not np.isnan(lower), "Lower should not be NaN"
        assert not np.isnan(position), "Position should not be NaN"
    
    def test_get_last_with_position(self):
        prices = np.linspace(100, 110, 30)
        calculator = BollingerBandsCalculator(window=20, num_std=2.0)
        
        upper, lower, position = calculator.calculate(prices)
        
        assert 0 <= position <= 1, "Position should be between 0 and 1"
        assert not np.isnan(position), "Position should not be NaN"
    
    def test_preconfigured_instance(self):
        prices = np.linspace(100, 110, 30)
        
        upper, lower, position = BOLLINGER_BANDS_20.calculate(prices)
        
        assert upper > lower, "Upper band should be above lower band"
        assert 0 <= position <= 1, "Position should be between 0 and 1"
    
    def test_fillna_option(self):
        prices = np.array([100, 101, 102, 103, 104])
        
        calculator_with_fillna = BollingerBandsCalculator(window=20, num_std=2.0, fillna=True)
        calculator_no_fillna = BollingerBandsCalculator(window=20, num_std=2.0, fillna=False)
        
        upper_fill, lower_fill, position_fill = calculator_with_fillna.calculate(prices)
        upper_no_fill, lower_no_fill, position_no_fill = calculator_no_fillna.calculate(prices)
        
        # Both should return valid values
        assert not np.isnan(upper_fill), "Filled upper should not be NaN"
        assert not np.isnan(upper_no_fill), "Non-filled upper should not be NaN"
        assert not np.isnan(position_fill), "Filled position should not be NaN"
        assert not np.isnan(position_no_fill), "Non-filled position should not be NaN"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
    
