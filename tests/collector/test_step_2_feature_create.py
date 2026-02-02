import sys
from pathlib import Path
import pytest
import pandas as pd

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from collect.candlestick_handler import candlestick_handler
from collect.normalization_handler import normalization_handler
from feature.feature_1h_creator import Feature1HCreator
from feature.feature_15m_creator import Feature15mCreator
from feature.feature_4h_creator import Feature4HCreator

class TestFeatureCreate:
    
    def test_1h_feature_create(self):
        candles = candlestick_handler.get_candlestick_data(inst_id = 'ETH-USDT-SWAP', bar = '1H', limit = 48)
        
        close = pd.Series(item['close'] for item in candles)
        volume = pd.Series(item['volume'] for item in candles)
        assert close is not None
        assert volume is not None
        is_close_saved = normalization_handler.get_normalization_params(inst_id = 'ETH-USDT-SWAP', bar = '1H', column = 'close')
        is_volume_saved = normalization_handler.get_normalization_params(inst_id = 'ETH-USDT-SWAP', bar = '1H', column = 'volume')
        
        creator = Feature1HCreator(close_mean = is_close_saved['mean'], 
                                    close_std = is_close_saved['std'], 
                                    vol_mean = is_volume_saved['mean'], 
                                    vol_std = is_volume_saved['std']);
        """
        Returns:
            Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
            "close_1h_normalized": Number,    // 价格标准化
            "volume_1h_normalized": Number,   // 成交量标准化
            "rsi_14_1h": Number,              // 标准短期动量指标
            "macd_line_1h": Number,           // MACD快线
            "macd_signal_1h": Number,         // MACD信号线
        """
        
        resultDict = creator.calculate(candles) 
        assert True
    
    def test_15m_feature_create(self):
        candles = candlestick_handler.get_candlestick_data(inst_id = 'ETH-USDT-SWAP', bar = '15m', limit = 48)
        
        close = pd.Series(item['close'] for item in candles)
        volume = pd.Series(item['volume'] for item in candles)
        assert close is not None
        assert volume is not None
        creator = Feature15mCreator();
        resultDict = creator.calculate(candles) 
        assert True
    
    def test_4h_feature_create(self):
        candles = candlestick_handler.get_candlestick_data(inst_id = 'ETH-USDT-SWAP', bar = '4H', limit = 48)
        
        close = pd.Series(item['close'] for item in candles)
        assert close is not None
        creator = Feature4HCreator();
        resultDict = creator.calculate(candles) 
        assert True
         
if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])