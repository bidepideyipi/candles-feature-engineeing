import sys
from pathlib import Path
import pandas as pd
import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from utils.impulse_calculator import IMPULSE_CALCULATOR


class TestImpulseCalculator:
    def test_calculate(self):
        # Create a sample volume series
        volume_series = pd.Series([1000, 1000, 1000, 1000, 1000, 1000, 2000,
                                   1000, 1000, 1000, 1000, 1000, 1000, 2000,
                                   1000, 1000, 1000, 1000, 1000, 1000, 2000,
                                   1000, 1000, 1000, 1000, 1000, 1000, 2000])
        
        # Calculate the impulse
        impulse = IMPULSE_CALCULATOR.calculate(volume_series)
        
        # Check the result
        assert impulse > 1.6 and impulse < 1.7

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])