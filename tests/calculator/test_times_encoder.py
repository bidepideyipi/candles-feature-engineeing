import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from utils.time_encoder import TIMESTAMP_ENCODER
import logging
logging.basicConfig(level=logging.DEBUG)

class TestTimesEncoder:
    def test_times_encoder(self):
        timestamps = [1769130000000, 1769126400000, 1769122800000,1769119200000, 
                      1769115600000, 1769112000000, 1769108400000, 1769104800000, 
                      1769091200000, 1769087600000, 1769084000000, 1769080400000, 
                      1769076800000, 1769073200000, 1769069600000, 1769066000000] 
        # Calculate hour cos and sin
        hour_cos, hour_sin = TIMESTAMP_ENCODER.calculate(timestamps)
        timestamps2 = [1769115600000, 1769112000000, 1769108400000, 1769104800000, 
                      1769091200000, 1769087600000, 1769084000000, 1769080400000, 
                      1769076800000, 1769073200000, 1769069600000, 1769066000000, 
                      1769062400000, 1769058800000, 1769055200000, 1769051600000] 
        hour_cos2, hour_sin2 = TIMESTAMP_ENCODER.calculate(timestamps2)
        # Show the day of the week for the timestamp
        w = pd.to_datetime(1769130000000).dayofweek
        
        # 根据数据hour_cos左移除4位应该等于hour_cos2右移除4位，hour_sin同理
        np.testing.assert_array_almost_equal(hour_cos[4:], hour_cos2[:-4])
        np.testing.assert_array_almost_equal(hour_sin[4:], hour_sin2[:-4])
        assert w == 3
        

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])