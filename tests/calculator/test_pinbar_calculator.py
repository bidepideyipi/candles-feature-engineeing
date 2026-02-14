"""
Pinbar Calculator Unit Tests
Test Pinbar calculation accuracy and edge cases
"""

import sys
from pathlib import Path
import numpy as np
import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from utils.pinbar_calculator import PINBAR_CALCULATOR


class TestPinbarCalculator:
    """Test suite for PinbarCalculator class"""
    
    def test_pinbar_normal_candle(self):
        """Test 1: Normal candle without long shadows"""
        high = [100, 102, 104, 106, 108]
        low = [98, 100, 102, 104, 106]
        open_prices = [99, 101, 103, 105, 107]
        close = [101, 103, 105, 107, 108]
        
        result = PINBAR_CALCULATOR.calculate(high, low, open_prices, close)
        
        assert result['upper_shadow'] >= 0, "Upper shadow should be non-negative"
        assert result['lower_shadow'] >= 0, "Lower shadow should be non-negative"
        assert result['body_height'] > 0, "Body height should be positive"
        assert result['body_ratio'] > 0, "Body ratio should be positive"
        print("✓ Test 1: Normal candle - PASSED")
        print(f"  Body ratio: {result['body_ratio']:.3f}")
        print(f"  Shadow imbalance: {result['shadow_imbalance']:.3f}")
        print(f"  Shadow type: {result['shadow_type']}")
        
    def test_pinbar_long_upper_shadow(self):
        """Test 2: Long upper shadow (bearish signal)"""
        high = [100, 102, 104, 106, 115]
        low = [98, 100, 102, 104, 106]
        open_prices = [99, 101, 103, 105, 107]
        close = [101, 103, 105, 107, 106]
        
        result = PINBAR_CALCULATOR.calculate(high, low, open_prices, close)
        
        assert result['upper_shadow'] > result['body_height'], "Upper shadow should be longer than body"
        assert result['is_long_upper_shadow'] == 1, "Should detect long upper shadow"
        assert result['shadow_type'] == 1, "Shadow type should be 1 (long upper shadow)"
        print("✓ Test 2: Long upper shadow - PASSED")
        print(f"  Upper shadow: {result['upper_shadow']:.2f}")
        print(f"  Body height: {result['body_height']:.2f}")
        print(f"  Shadow type: {result['shadow_type']}")
        
    def test_pinbar_long_lower_shadow(self):
        """Test 3: Long lower shadow (bullish signal)"""
        high = [100, 102, 104, 106, 108]
        low = [98, 96, 94, 92, 95]
        open_prices = [99, 101, 103, 105, 107]
        close = [101, 103, 105, 107, 106]
        
        result = PINBAR_CALCULATOR.calculate(high, low, open_prices, close)
        
        assert result['lower_shadow'] > result['body_height'], "Lower shadow should be longer than body"
        assert result['is_long_lower_shadow'] == 1, "Should detect long lower shadow"
        assert result['shadow_type'] == 2, "Shadow type should be 2 (long lower shadow)"
        print("✓ Test 3: Long lower shadow - PASSED")
        print(f"  Lower shadow: {result['lower_shadow']:.2f}")
        print(f"  Body height: {result['body_height']:.2f}")
        print(f"  Shadow type: {result['shadow_type']}")
        
    def test_pinbar_doji(self):
        """Test 4: Doji candle (small body, potential reversal)"""
        high = [100, 102, 104, 106, 110]
        low = [98, 100, 102, 104, 95]
        open_prices = [99, 101, 103, 105, 102.5]
        close = [101, 103, 105, 107, 102.6]
        
        result = PINBAR_CALCULATOR.calculate(high, low, open_prices, close)
        
        assert result['is_doji'] == 1, "Should detect doji pattern"
        assert result['body_ratio'] < 0.2, "Body ratio should be small for doji"
        print("✓ Test 4: Doji pattern - PASSED")
        print(f"  Body ratio: {result['body_ratio']:.3f}")
        print(f"  Is doji: {result['is_doji']}")
        
    def test_pinbar_bullish_engulfing(self):
        """Test 5: Bullish engulfing pattern (long lower shadow + small upper shadow)"""
        high = [100, 102, 104, 106, 108]
        low = [98, 95, 92, 89, 90]
        open_prices = [99, 101, 103, 105, 95]
        close = [101, 103, 105, 107, 104]
        
        result = PINBAR_CALCULATOR.calculate(high, low, open_prices, close)
        
        assert result['shadow_imbalance'] < 0, "Should have positive imbalance (lower shadow > upper shadow)"
        print("✓ Test 5: Bullish pattern - PASSED")
        print(f"  Shadow imbalance: {result['shadow_imbalance']:.3f}")
        print(f"  Lower shadow ratio: {result['lower_shadow_ratio']:.3f}")
        
    def test_pinbar_bearish_engulfing(self):
        """Test 6: Bearish engulfing pattern (long upper shadow + small lower shadow)"""
        high = [100, 105, 110, 115, 120]
        low = [98, 99, 100, 101, 105]
        open_prices = [99, 101, 103, 105, 110]
        close = [101, 103, 105, 107, 108]
        
        result = PINBAR_CALCULATOR.calculate(high, low, open_prices, close)
        
        assert result['shadow_imbalance'] > 0, "Should have negative imbalance (upper shadow > lower shadow)"
        assert result['is_long_upper_shadow'] == 1, "Should detect long upper shadow"
        print("✓ Test 6: Bearish pattern - PASSED")
        print(f"  Shadow imbalance: {result['shadow_imbalance']:.3f}")
        print(f"  Upper shadow ratio: {result['upper_shadow_ratio']:.3f}")
        
    def test_pinbar_both_long_shadows(self):
        """Test 7: Both upper and lower shadows long (market indecision)"""
        high = [100, 105, 110, 115, 120]
        low = [98, 95, 90, 85, 90]
        open_prices = [99, 101, 103, 105, 105]
        close = [101, 103, 105, 107, 105]
        
        result = PINBAR_CALCULATOR.calculate(high, low, open_prices, close)
        
        assert result['is_long_upper_shadow'] == 1, "Should detect long upper shadow"
        assert result['is_long_lower_shadow'] == 1, "Should detect long lower shadow"
        assert result['shadow_type'] == 3, "Shadow type should be 3 (both shadows long)"
        print("✓ Test 7: Both shadows long - PASSED")
        print(f"  Shadow type: {result['shadow_type']}")
        print(f"  Total shadow ratio: {result['total_shadow_ratio']:.3f}")
        
    def test_pinbar_empty_data(self):
        """Test 8: Empty data"""
        result = PINBAR_CALCULATOR.calculate([], [], [], [])
        
        assert result['upper_shadow'] == 0, "Should return 0 for empty data"
        assert result['lower_shadow'] == 0, "Should return 0 for empty data"
        assert result['body_height'] == 0, "Should return 0 for empty data"
        print("✓ Test 8: Empty data - PASSED")
        
    def test_pinbar_single_candle(self):
        """Test 9: Single candle"""
        high = [105]
        low = [95]
        open_prices = [100]
        close = [102]
        
        result = PINBAR_CALCULATOR.calculate(high, low, open_prices, close)
        
        assert result['upper_shadow'] == 3, "Upper shadow should be 3 (105-102)"
        assert result['lower_shadow'] == 5, "Lower shadow should be 5 (100-95)"
        assert result['body_height'] == 2, "Body height should be 2 (102-100)"
        assert result['body_ratio'] == 0.2, "Body ratio should be 0.2 (2/10)"
        print("✓ Test 9: Single candle - PASSED")
        print(f"  All calculations correct")


if __name__ == "__main__":
    # Run tests
    print("\n" + "=" * 60)
    print("Pinbar Calculator Unit Tests")
    print("=" * 60 + "\n")
    
    pytest.main([__file__, "-v", "-s"])
