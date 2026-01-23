#!/usr/bin/env python3
"""
Demonstration of the new assembly pattern for TechnicalIndicatorsCalculator
Shows how to flexibly add/remove indicators without modifying internal code
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Mock pandas and numpy for demonstration
class MockDataFrame:
    def __init__(self, data):
        self.data = data
        self.columns = list(data.keys()) if data else []
    
    def tail(self, n):
        # Simple mock implementation
        return MockDataFrame({k: v[-n:] if hasattr(v, '__getitem__') else v for k, v in self.data.items()})
    
    def sort_values(self, column):
        return self
    
    def reset_index(self, drop=True):
        return self
    
    def __len__(self):
        return len(next(iter(self.data.values()))) if self.data else 0

class MockSeries:
    def __init__(self, data):
        self.data = data
    
    def iloc(self, index):
        if isinstance(index, slice):
            return MockSeries(self.data[index])
        return self.data[index] if index < len(self.data) else None
    
    def diff(self):
        return MockSeries([0] + [self.data[i] - self.data[i-1] for i in range(1, len(self.data))])
    
    def where(self, condition, other):
        if callable(condition):
            result = []
            for i, val in enumerate(self.data):
                if condition(val):
                    result.append(val)
                else:
                    result.append(other)
            return MockSeries(result)
        return self
    
    def rolling(self, window, min_periods=1):
        return MockRolling(self.data, window, min_periods)
    
    def ewm(self, span, adjust=False):
        return MockEWM(self.data, span)
    
    def pct_change(self):
        return MockSeries([0] + [(self.data[i]/self.data[i-1] - 1) for i in range(1, len(self.data))])
    
    def dropna(self):
        return MockSeries([x for x in self.data if x is not None and not (isinstance(x, float) and str(x) == 'nan')])
    
    def std(self):
        if not self.data:
            return 0
        mean = sum(self.data) / len(self.data)
        return (sum((x - mean) ** 2 for x in self.data) / len(self.data)) ** 0.5
    
    def mean(self):
        return sum(self.data) / len(self.data) if self.data else 0

class MockRolling:
    def __init__(self, data, window, min_periods):
        self.data = data
        self.window = window
        self.min_periods = min_periods
    
    def mean(self):
        result = []
        for i in range(len(self.data)):
            if i + 1 < self.min_periods:
                result.append(None)
            else:
                start = max(0, i - self.window + 1)
                window_data = self.data[start:i+1]
                result.append(sum(window_data) / len(window_data))
        return MockSeries(result)

class MockEWM:
    def __init__(self, data, span):
        self.data = data
        self.span = span
    
    def mean(self):
        # Simplified EMA calculation
        result = [self.data[0]]
        multiplier = 2 / (self.span + 1)
        for i in range(1, len(self.data)):
            ema = (self.data[i] * multiplier) + (result[-1] * (1 - multiplier))
            result.append(ema)
        return MockSeries(result)

# Mock pandas and numpy modules
import types
mock_pd = types.ModuleType('pandas')
mock_pd.DataFrame = MockDataFrame
mock_pd.Series = MockSeries

mock_np = types.ModuleType('numpy')
mock_np.nan = float('nan')
mock_np.random = types.ModuleType('random')
mock_np.random.normal = lambda loc, scale, size: [loc + scale * 0.1 for _ in range(size)] if isinstance(size, int) else [[loc + scale * 0.1 for _ in range(size[1])] for _ in range(size[0])]
mock_np.random.uniform = lambda low, high, size: [low + (high-low)*0.5 for _ in range(size)]
mock_np.sqrt = lambda x: x ** 0.5
mock_np.std = lambda x: (sum((i - sum(x)/len(x))**2 for i in x)/len(x))**0.5 if x else 0
mock_np.mean = lambda x: sum(x)/len(x) if x else 0
mock_np.isnan = lambda x: str(x) == 'nan' or x is None

import sys
sys.modules['pandas'] = mock_pd
sys.modules['numpy'] = mock_np

from src.feature.technical_indicators import (
    TechnicalIndicatorsCalculator, 
    create_custom_calculator,
    get_available_indicators
)
from src.feature.indicator_interface import indicator_registry
from src.feature.indicators import RSIIndicator, MACDIndicator, BollingerBandsIndicator


def create_sample_data():
    """Create sample OHLCV data for testing"""
    # Generate realistic price data using mock random
    prices = [100]
    for i in range(99):
        # Simple random walk
        change = (i % 10 - 5) * 0.01  # Deterministic pattern for consistency
        prices.append(prices[-1] * (1 + change))
    
    # Create DataFrame-like structure
    data = {
        'timestamp': list(range(100)),  # Mock timestamps
        'open': prices[:-1],
        'high': [p * 1.01 for p in prices[:-1]],  # Simple high
        'low': [p * 0.99 for p in prices[:-1]],   # Simple low
        'close': prices[1:],
        'volume': [5000 + (i % 1000) for i in range(99)]  # Mock volume
    }
    
    return MockDataFrame(data)


def demonstrate_assembly_pattern():
    """Demonstrate the flexible assembly pattern"""
    
    print("=== Technical Indicators Assembly Pattern Demo ===\n")
    
    # 1. Show available indicators
    print("1. Available Indicators:")
    available = get_available_indicators()
    for indicator in available:
        print(f"   - {indicator}")
    print()
    
    # 2. Default calculator (backward compatibility)
    print("2. Default Calculator (backward compatible):")
    default_calc = TechnicalIndicatorsCalculator()
    print(f"   Indicators: {default_calc.list_indicators()}")
    
    sample_data = create_sample_data()
    results = default_calc.calculate_indicators(sample_data.tail(50))
    print(f"   Sample results keys: {list(results.keys())[:10]}...")  # Show first 10 keys
    print()
    
    # 3. Custom calculator with selected indicators
    print("3. Custom Calculator (only RSI and BB):")
    custom_calc = TechnicalIndicatorsCalculator([
        RSIIndicator(window=14),
        BollingerBandsIndicator(window=20, num_std=2.0)
    ])
    print(f"   Indicators: {custom_calc.list_indicators()}")
    
    custom_results = custom_calc.calculate_indicators(sample_data.tail(50))
    print(f"   Sample results keys: {list(custom_results.keys())[:8]}...")  # Show first 8 keys
    print()
    
    # 4. Dynamic indicator management
    print("4. Dynamic Indicator Management:")
    dynamic_calc = TechnicalIndicatorsCalculator()
    print(f"   Initial indicators: {dynamic_calc.list_indicators()}")
    
    # Remove an indicator
    dynamic_calc.remove_indicator("MACD")
    print(f"   After removing MACD: {dynamic_calc.list_indicators()}")
    
    # Add a new indicator
    dynamic_calc.add_indicator("Volatility", window=14)
    print(f"   After adding Volatility: {dynamic_calc.list_indicators()}")
    print()
    
    # 5. Using convenience function
    print("5. Using Convenience Function:")
    convenience_calc = create_custom_calculator(
        ["RSI", "PricePosition"],
        RSI={"window": 9},  # Custom RSI parameters
        PricePosition={"window": 10}  # Custom PricePosition parameters
    )
    print(f"   Indicators: {convenience_calc.list_indicators()}")
    
    convenience_results = convenience_calc.calculate_indicators(sample_data.tail(30))
    print(f"   Sample results: {list(convenience_results.keys())}")


def demonstrate_flexibility():
    """Show how easy it is to experiment with different indicator combinations"""
    
    print("\n=== Flexibility Demonstration ===\n")
    
    sample_data = create_sample_data().tail(40)
    
    # Different experimental setups
    experiments = [
        {
            "name": "Minimal Setup",
            "indicators": ["RSI"]
        },
        {
            "name": "Trend Following",
            "indicators": ["MACD", "PricePosition"]
        },
        {
            "name": "Volatility Analysis",
            "indicators": ["BB", "Volatility"]
        },
        {
            "name": "Complete Setup",
            "indicators": ["RSI", "MACD", "BB", "PricePosition", "Volatility"]
        }
    ]
    
    for exp in experiments:
        print(f"{exp['name']}:")
        calc = create_custom_calculator(exp["indicators"])
        results = calc.calculate_indicators(sample_data)
        print(f"   Indicators: {calc.list_indicators()}")
        print(f"   Result count: {len(results)} features")
        print(f"   Feature names: {list(results.keys())[:5]}...")
        print()


if __name__ == "__main__":
    demonstrate_assembly_pattern()
    demonstrate_flexibility()
    print("=== Demo Complete ===")