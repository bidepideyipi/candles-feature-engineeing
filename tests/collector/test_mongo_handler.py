import sys
from pathlib import Path
import pytest
import pandas as pd

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from collect.candlestick_handler import candlestick_handler
from collect.normalization_handler import normalization_handler
from utils.normalize_encoder import NORMALIZED

class TestMongoHandler:
    
    def test_candlestick_handler(self):
        candles = candlestick_handler.get_candlestick_data(inst_id = 'ETH-USDT-SWAP', bar = '1H', limit = 5000)
        
        close = pd.Series(item['close'] for item in candles)
        volume = pd.Series(item['volume'] for item in candles)
        assert close is not None
        assert volume is not None
        _, mean_close, std = NORMALIZED.calculate(close)
        _, mean_volume, std_volume  = NORMALIZED.calculate(volume)
        is_close_saved = normalization_handler.save_normalization_params(inst_id = 'ETH-USDT-SWAP', bar = '1H', column = 'close', mean = mean_close, std = std)
        is_volume_saved = normalization_handler.save_normalization_params(inst_id = 'ETH-USDT-SWAP', bar = '1H', column = 'volume', mean = mean_volume, std = std_volume)
        assert is_close_saved is True
        assert is_volume_saved is True
        
    def test_normalization_handler(self):
        normalized_close = normalization_handler.get_normalization_params(inst_id = 'ETH-USDT-SWAP', bar = '1H', column = 'close')
        normalized_volume = normalization_handler.get_normalization_params(inst_id = 'ETH-USDT-SWAP', bar = '1H', column = 'volume')
        assert normalized_close is not None
        assert normalized_volume is not None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])