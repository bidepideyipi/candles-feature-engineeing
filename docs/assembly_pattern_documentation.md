# Technical Indicators Assembly Pattern Documentation

## Overview

The `TechnicalIndicatorsCalculator` has been refactored to use an **assembly pattern** that allows flexible addition/removal of technical indicators without modifying internal code. This makes it easy to experiment with different indicator combinations during feature engineering.

## Key Benefits

### 1. **Flexibility**
- Add/remove indicators dynamically
- No need to modify calculator internals
- Easy experimentation with different indicator sets

### 2. **Maintainability**
- Clean separation of concerns
- Each indicator is self-contained
- Easy to test individual indicators

### 3. **Extensibility**
- New indicators can be registered easily
- Consistent interface for all indicators
- Backward compatibility maintained

## Architecture

### Component Structure

```
src/feature/
├── indicator_interface.py      # Abstract base classes and registry
├── indicators.py               # Concrete indicator implementations
└── technical_indicators.py     # Main calculator using assembly pattern
```

### Key Components

1. **`TechnicalIndicator`** (Abstract Base Class)
   - Defines the contract for all indicators
   - Standard result format via `IndicatorResult`
   - Required methods: `calculate()`, `required_columns`, `min_periods`

2. **`IndicatorRegistry`**
   - Central registry for all available indicators
   - Enables dynamic indicator discovery
   - Supports both class registration and instance creation

3. **`TechnicalIndicatorsCalculator`** (Assembly Pattern)
   - Manages a collection of indicator instances
   - Provides methods to add/remove indicators
   - Calculates all configured indicators for each time window

## Usage Examples

### 1. Default Usage (Backward Compatible)

```python
from src.feature.technical_indicators import tech_calculator
import pandas as pd

# Works exactly like before
df = pd.DataFrame(...)  # Your OHLCV data
indicators = tech_calculator.calculate_indicators(df)
```

### 2. Custom Indicator Selection

```python
from src.feature.technical_indicators import TechnicalIndicatorsCalculator
from src.feature.indicators import RSIIndicator, BollingerBandsIndicator

# Create calculator with only specific indicators
calc = TechnicalIndicatorsCalculator([
    RSIIndicator(window=14),
    BollingerBandsIndicator(window=20, num_std=2.0)
])

results = calc.calculate_indicators(df)
```

### 3. Dynamic Indicator Management

```python
from src.feature.technical_indicators import TechnicalIndicatorsCalculator

# Start with default indicators
calc = TechnicalIndicatorsCalculator()

# Remove unwanted indicators
calc.remove_indicator("MACD")

# Add new indicators
calc.add_indicator("Volatility", window=14)

# Check current configuration
print(calc.list_indicators())
```

### 4. Using Convenience Functions

```python
from src.feature.technical_indicators import create_custom_calculator

# Create calculator with named indicators and custom parameters
calc = create_custom_calculator(
    ["RSI", "PricePosition", "Volatility"],
    RSI={"window": 9},              # Custom RSI parameters
    PricePosition={"window": 10},   # Custom PricePosition parameters
    Volatility={"window": 20}       # Custom Volatility parameters
)
```

### 5. Experimenting with Different Combinations

```python
# Different experimental setups
setups = [
    ["RSI"],                                    # Minimal
    ["MACD", "PricePosition"],                 # Trend following
    ["BB", "Volatility"],                      # Volatility analysis
    ["RSI", "MACD", "BB", "PricePosition"]     # Comprehensive
]

for setup in setups:
    calc = create_custom_calculator(setup)
    results = calc.calculate_indicators(df)
    print(f"Setup {setup}: {len(results)} features generated")
```

## Available Indicators

### Built-in Indicators

1. **RSIIndicator** - Relative Strength Index
   - Parameters: `window` (default: 14)
   - Output: `rsi`

2. **MACDIndicator** - Moving Average Convergence Divergence
   - Parameters: `fast_window` (12), `slow_window` (26), `signal_window` (9)
   - Output: `macd_line`, `macd_signal`, `macd_histogram`

3. **BollingerBandsIndicator** - Bollinger Bands
   - Parameters: `window` (20), `num_std` (2.0)
   - Output: `bb_upper`, `bb_middle`, `bb_lower`, `bb_position`

4. **PricePositionIndicator** - Price relative to moving average
   - Parameters: `window` (20)
   - Output: `priceposition`

5. **VolatilityIndicator** - Price volatility
   - Parameters: `window` (24)
   - Output: `volatility`

## Adding New Indicators

### 1. Create Indicator Class

```python
from src.feature.indicator_interface import TechnicalIndicator, IndicatorResult
from src.feature.indicator_interface import indicator_registry

@indicator_registry.register
class MyNewIndicator(TechnicalIndicator):
    def __init__(self, param1: int = 10, name: str = "MyIndicator"):
        super().__init__(name)
        self.param1 = param1
    
    def calculate(self, df: pd.DataFrame) -> IndicatorResult:
        # Your calculation logic here
        result_value = your_calculation(df['close'])
        
        return IndicatorResult(
            name=self.name,
            values={'myindicator': float(result_value)},
            metadata={'param1': self.param1}
        )
    
    @property
    def required_columns(self) -> List[str]:
        return ['close']
    
    @property
    def min_periods(self) -> int:
        return self.param1
```

### 2. Use Your New Indicator

```python
# Your new indicator is automatically available
calc = create_custom_calculator(["MyIndicator"], 
                               MyIndicator={"param1": 15})
```

## Migration Guide

### From Old Approach (Hardcoded Indicators)

```python
# OLD - Indicators hardcoded in _calculate_window_indicators method
def _calculate_window_indicators(self, df, window_name):
    # RSI calculation code here
    # MACD calculation code here
    # Bollinger Bands calculation code here
    # ... lots of code to modify when changing indicators
```

### To New Approach (Assembly Pattern)

```python
# NEW - Indicators assembled dynamically
calc = TechnicalIndicatorsCalculator([
    RSIIndicator(window=14),
    MACDIndicator(fast_window=12, slow_window=26, signal_window=9),
    BollingerBandsIndicator(window=20, num_std=2.0)
])

# To change indicators, just modify the list - no internal code changes!
```

## Best Practices

### 1. **Experimentation Workflow**
```python
# Start with minimal setup
minimal_calc = create_custom_calculator(["RSI"])

# Test performance
score1 = evaluate_model(minimal_calc)

# Add more indicators
extended_calc = create_custom_calculator(["RSI", "MACD", "BB"])
score2 = evaluate_model(extended_calc)

# Compare results and iterate
```

### 2. **Performance Considerations**
```python
# Some indicators are computationally expensive
# Start with lightweight indicators for rapid iteration
fast_indicators = ["RSI", "PricePosition"]
slow_indicators = ["MACD", "BB"]  # More computationally intensive

# Use fast indicators during development
dev_calc = create_custom_calculator(fast_indicators)
```

### 3. **Feature Selection**
```python
# The assembly pattern makes it easy to test feature importance
all_indicators = ["RSI", "MACD", "BB", "PricePosition", "Volatility"]

# Test different combinations systematically
for i in range(1, len(all_indicators) + 1):
    for combo in combinations(all_indicators, i):
        calc = create_custom_calculator(list(combo))
        # Evaluate model performance
```

This assembly pattern provides unprecedented flexibility for technical analysis feature engineering while maintaining clean, maintainable code structure.