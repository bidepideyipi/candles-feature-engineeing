"""
EMA Calculator Unit Tests
Test EMA calculation accuracy and edge cases
"""

import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from utils.ema_calculator import (
    EMA_12, EMA_26, EMA_48,
    EMA_CROSSOVER_12_26, EMA_CROSSOVER_26_48,
    EMACrossoverSignal
)


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
    
    def test_ema_48_period(self):
        prices = np.linspace(100, 200, 60)
        result = EMA_48.calculate(prices)
        assert result > 100 and result < 200, "EMA 48 should be within price range"
    
    def test_insufficient_data(self):
        with pytest.raises(ValueError):
            EMA_12.calculate(np.array([100, 101, 102]))


class TestEMACrossoverSignal:
    """Test suite for EMA Crossover Signal class"""
    
    def test_crossover_12_26_bullish(self):
        prices = np.concatenate([np.linspace(100, 90, 20), np.linspace(90, 110, 20)])
        ema_12_value = EMA_12.calculate(prices)
        ema_26_value = EMA_26.calculate(prices)
        signal = EMACrossoverSignal.calculate_from_values(ema_12_value, ema_26_value)
        assert signal == 1, "Fast EMA should be above slow EMA after upward move"
    
    def test_crossover_12_26_bearish(self):
        prices = np.concatenate([np.linspace(110, 90, 20), np.linspace(90, 80, 20)])
        ema_12_value = EMA_12.calculate(prices)
        ema_26_value = EMA_26.calculate(prices)
        signal = EMACrossoverSignal.calculate_from_values(ema_12_value, ema_26_value)
        assert signal == -1, "Fast EMA should be below slow EMA after downward move"
    
    def test_crossover_26_48_bullish(self):
        prices = np.linspace(100, 200, 60)
        ema_26_value = EMA_26.calculate(prices)
        ema_48_value = EMA_48.calculate(prices)
        signal = EMACrossoverSignal.calculate_from_values(ema_26_value, ema_48_value)
        assert signal == 1, "Fast EMA should be above slow EMA in upward trend"
    
    def test_crossover_26_48_bearish(self):
        prices = np.linspace(200, 100, 60)
        ema_26_value = EMA_26.calculate(prices)
        ema_48_value = EMA_48.calculate(prices)
        signal = EMACrossoverSignal.calculate_from_values(ema_26_value, ema_48_value)
        assert signal == -1, "Fast EMA should be below slow EMA in downward trend"
    
    def test_crossover_neutral(self):
        prices = np.linspace(100, 100, 30)
        ema_12_value = EMA_12.calculate(prices)
        ema_26_value = EMA_26.calculate(prices)
        signal = EMACrossoverSignal.calculate_from_values(ema_12_value, ema_26_value)
        assert signal == 0, "EMAs should be equal when prices are constant"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
