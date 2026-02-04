import sys
from pathlib import Path
import pytest
import pandas as pd
import logging

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from collect.okex_fetcher import okex_fetcher
from collect.candlestick_handler import candlestick_handler

# 增强日志配置
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # 确保日志输出到标准输出
    ]
)

# 为 okex_fetcher 模块单独设置日志级别
okex_logger = logging.getLogger('collect.okex_fetcher')
okex_logger.setLevel(logging.DEBUG)

class TestCandlestickHandler:
        
    def test_fetcher_data(self):
        
        # 默认拉10万条，测试的时候可以少拉一些
        okex_fetcher.fetch_historical_data(inst_id="ETH-USDT-SWAP", bar="1D", max_records=600)
        okex_fetcher.fetch_historical_data(inst_id="ETH-USDT-SWAP", bar="4H", max_records=3600)
        okex_fetcher.fetch_historical_data(inst_id="ETH-USDT-SWAP", bar="1H", max_records=14400)
        okex_fetcher.fetch_historical_data(inst_id="ETH-USDT-SWAP", bar="15m", max_records=57600)
        
        count_15m_after = candlestick_handler.count(inst_id="ETH-USDT-SWAP", bar="15m")
        count_1H_after = candlestick_handler.count(inst_id="ETH-USDT-SWAP", bar="1H")
        count_4H_after = candlestick_handler.count(inst_id="ETH-USDT-SWAP", bar="4H")
        count_1D_after = candlestick_handler.count(inst_id="ETH-USDT-SWAP", bar="1D")
        logging.info(f"15m: {count_15m_after}, 1H: {count_1H_after}, 4H: {count_4H_after}, 1D: {count_1D_after}")
        
        assert True

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])