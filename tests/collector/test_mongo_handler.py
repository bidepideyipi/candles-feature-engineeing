import sys
from pathlib import Path
import pytest
import pandas as pd

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from collect.candlestick_handler import candlestick_handler
from collect.normalization_handler import normalization_handler

class TestMongoHandler:
    
    def test_candlestick_handler(self):
        candles = candlestick_handler.get_candlestick_data(inst_id = 'ETH-USDT-SWAP', bar = '1H', limit = 5000)
        
        close = pd.Series(item['close'] for item in candles)
        volume = pd.Series(item['volume'] for item in candles)
        assert close is not None
        assert volume is not None
        assert candles is not None
        assert len(candles) > 0
        
    def test_normalization_handler(self):
        normalized_data = normalization_handler.normalize_data(inst_id = 'ETH-USDT-SWAP', bar = '1H')
        assert normalized_data is not None
        assert len(normalized_data) > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])