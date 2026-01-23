# Technical Indicators Refactoring Documentation

## Overview

The technical indicators calculation has been refactored to create independent, reusable calculator classes for RSI, MACD, and Bollinger Bands. This improves modularity, testability, and maintainability.

## New Structure

### Utils Directory
Created `src/utils/` directory containing independent calculator classes:

```
src/utils/
├── __init__.py
├── rsi_calculator.py              # RSI calculation utilities
├── macd_calculator.py             # MACD calculation utilities  
├── bollinger_bands_calculator.py  # Bollinger Bands calculation utilities
```

### Feature Directory
Updated `src/feature/technical_indicators.py` to use the new independent calculators.

## Independent Calculator Classes

### 1. RSICalculator (`src/utils/rsi_calculator.py`)

**Features:**
- Independent RSI calculation with customizable window size
- Configurable NaN handling
- Both class-based and functional interfaces

**Usage:**
```python
from src.utils.rsi_calculator import RSICalculator

# Class-based usage
rsi_calc = RSICalculator(window=14)
rsi_values = rsi_calc.calculate(close_prices)
last_rsi = rsi_calc.get_last_value(close_prices)

# Functional usage
from src.utils.rsi_calculator import calculate_rsi, get_rsi_last
rsi_values = calculate_rsi(close_prices, window=14)
last_rsi = get_rsi_last(close_prices, window=14)
```

### 2. MACDCalculator (`src/utils/macd_calculator.py`)

**Features:**
- Independent MACD calculation with customizable parameters
- Configurable fast, slow, and signal window sizes
- Returns MACD line, signal line, and histogram
- Both class-based and functional interfaces

**Usage:**
```python
from src.utils.macd_calculator import MACDCalculator

# Class-based usage
macd_calc = MACDCalculator(fast_window=12, slow_window=26, signal_window=9)
macd_line, signal_line, histogram = macd_calc.calculate(close_prices)
last_values = macd_calc.get_last_values(close_prices)

# Functional usage
from src.utils.macd_calculator import calculate_macd, get_macd_last
macd_line, signal_line, histogram = calculate_macd(close_prices)
last_macd, last_signal, last_hist = get_macd_last(close_prices)
```

### 3. BollingerBandsCalculator (`src/utils/bollinger_bands_calculator.py`)

**Features:**
- Independent Bollinger Bands calculation
- Configurable window size and standard deviation multiplier
- Option to calculate band position (0-1 scale)
- Both class-based and functional interfaces

**Usage:**
```python
from src.utils.bollinger_bands_calculator import BollingerBandsCalculator

# Class-based usage
boll_calc = BollingerBandsCalculator(window=20, num_std=2.0)
upper, middle, lower = boll_calc.calculate(close_prices)
upper, middle, lower, position = boll_calc.calculate_with_position(close_prices)

# Functional usage
from src.utils.bollinger_bands_calculator import calculate_bollinger_bands, get_bollinger_bands_last
upper, middle, lower = calculate_bollinger_bands(close_prices)
last_upper, last_middle, last_lower, last_pos = get_bollinger_bands_last_with_position(close_prices)
```

## Benefits

### 1. **Independence**
- Each indicator is completely independent
- No coupling with the main system configuration
- Can be used standalone in any project

### 2. **Customizability**
- All parameters are configurable
- Flexible window sizes and calculation parameters
- Optional NaN filling behavior

### 3. **Multiple Interfaces**
- Class-based approach for complex usage
- Functional convenience functions for simple cases
- Consistent API across all indicators

### 4. **Better Error Handling**
- Proper NaN value handling
- Division by zero protection
- Graceful error recovery

### 5. **Improved Testability**
- Each calculator can be tested independently
- Mock data can be easily used for testing
- Clear separation of concerns

## Migration Guide

### Before (Old Approach):
```python
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands

# RSI
rsi_indicator = RSIIndicator(close=close_prices, window=14)
rsi_values = rsi_indicator.rsi()

# MACD
macd_indicator = MACD(close=close_prices, window_fast=12, window_slow=26, window_sign=9)
macd_line = macd_indicator.macd()
signal_line = macd_indicator.macd_signal()
histogram = macd_indicator.macd_diff()

# Bollinger Bands
bb_indicator = BollingerBands(close=close_prices, window=20, window_dev=2)
upper_band = bb_indicator.bollinger_hband()
middle_band = bb_indicator.bollinger_mavg()
lower_band = bb_indicator.bollinger_lband()
```

### After (New Approach):
```python
from src.utils.rsi_calculator import RSICalculator
from src.utils.macd_calculator import MACDCalculator
from src.utils.bollinger_bands_calculator import BollingerBandsCalculator

# RSI
rsi_calc = RSICalculator(window=14)
rsi_value = rsi_calc.get_last_value(close_prices)

# MACD
macd_calc = MACDCalculator(fast_window=12, slow_window=26, signal_window=9)
macd_line, signal_line, histogram = macd_calc.get_last_values(close_prices)

# Bollinger Bands
boll_calc = BollingerBandsCalculator(window=20, num_std=2.0)
upper_band, middle_band, lower_band, position = boll_calc.get_last_with_position(close_prices)
```

## Testing

Each calculator includes comprehensive error handling and can be easily tested:

```python
# Example test
def test_rsi_calculator():
    prices = [100, 101, 102, 101, 100, 99, 98, 99, 100, 101]
    rsi_calc = RSICalculator(window=5)
    result = rsi_calc.calculate(prices)
    assert len(result) == len(prices)
    assert not result.isna().all()
```

The refactored approach provides a cleaner, more maintainable, and more flexible foundation for technical analysis calculations.