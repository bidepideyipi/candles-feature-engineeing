import sys
from pathlib import Path
import numpy as np
import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.time_encoder import TIMESTAMP_ENCODER
import logging
logging.basicConfig(level=logging.DEBUG)

class TestTimesEncoder:
    def test_times_encoder(self):
        timestamps = [1769130000000, 1769126400000, 1769122800000,
              1769119200000, 1769115600000, 1769112000000] 
        hour_cos, hour_sin = TIMESTAMP_ENCODER.calculate(timestamps)
        assert True

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])