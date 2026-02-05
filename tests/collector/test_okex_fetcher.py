"""
OKEx Fetcher Unit Tests
Test API data fetching functionality
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from collect.okex_fetcher import okex_fetcher

class TestOKExFetcher:
    """Test suite for OKExDataFetcher class"""
    
    def test_fetch_realtime_candles(self):
        """Test fetching realtime candlestick data."""
        print("\n=== Testing realtime candle fetch ===")
        
        results = okex_fetcher.fetch_realtime_candles(inst_id="ETH-USDT-SWAP")
        
        # Check that all timeframes are present
        expected_timeframes = ["15m", "1H", "4H", "1D"]
        for tf in expected_timeframes:
            assert tf in results, f"Timeframe {tf} should be in results"
            print(f"✓ {tf}: {len(results[tf])} candles fetched")
        
        # Check that each timeframe returns a list
        for tf in expected_timeframes:
            assert isinstance(results[tf], list), f"{tf} should return a list"
        
        # Check that each candle has required fields (raw array format)
        for tf in expected_timeframes:
            if results[tf]:
                sample_candle = results[tf][0]
                assert len(sample_candle) >= 9, f"Sample candle should have at least 9 fields, got {len(sample_candle)}"
                print(f"✓ {tf} sample candle has {len(sample_candle)} fields")
        
        print(f"\n✓ All timeframes fetched successfully")


if __name__ == "__main__":
    test = TestOKExFetcher()
    test.test_fetch_realtime_candles()
    print("\n✓ All tests passed!")
