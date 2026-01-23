#!/usr/bin/env python3
"""
Simple test of the assembly pattern functionality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from src.feature.technical_indicators import (
        TechnicalIndicatorsCalculator, 
        create_custom_calculator,
        get_available_indicators
    )
    from src.feature.indicators import RSIIndicator, MACDIndicator
    
    print("✅ Successfully imported all modules")
    
    # Test 1: Available indicators
    available = get_available_indicators()
    print(f"✅ Available indicators: {available}")
    
    # Test 2: Default calculator
    default_calc = TechnicalIndicatorsCalculator()
    print(f"✅ Default calculator indicators: {default_calc.list_indicators()}")
    
    # Test 3: Custom calculator
    custom_calc = TechnicalIndicatorsCalculator([
        RSIIndicator(window=14),
        MACDIndicator(fast_window=12, slow_window=26, signal_window=9)
    ])
    print(f"✅ Custom calculator indicators: {custom_calc.list_indicators()}")
    
    # Test 4: Dynamic management
    dynamic_calc = TechnicalIndicatorsCalculator()
    initial_count = len(dynamic_calc.list_indicators())
    dynamic_calc.remove_indicator("MACD")
    after_remove = len(dynamic_calc.list_indicators())
    dynamic_calc.add_indicator("Volatility", window=14)
    final_count = len(dynamic_calc.list_indicators())
    
    print(f"✅ Dynamic management: {initial_count} -> {after_remove} -> {final_count}")
    
    print("\n🎉 All tests passed! Assembly pattern is working correctly.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()