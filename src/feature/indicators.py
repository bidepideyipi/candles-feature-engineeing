"""
Concrete Technical Indicator Implementations
Implementation of various technical indicators using the interface
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from .indicator_interface import TechnicalIndicator, IndicatorResult, indicator_registry
from ..utils.rsi_calculator import RSICalculator
from ..utils.macd_calculator import MACDCalculator
from ..utils.bollinger_bands_calculator import BollingerBandsCalculator


@indicator_registry.register
class RSIIndicator(TechnicalIndicator):
    """RSI (Relative Strength Index) Indicator"""
    
    def __init__(self, window: int = 14, name: str = "RSI"):
        super().__init__(name)
        self.window = window
        self.calculator = RSICalculator(window=window)
    
    def calculate(self, df: pd.DataFrame) -> IndicatorResult:
        close_prices = df['close']
        rsi_value = self.calculator.get_last_value(close_prices)
        
        values = {
            f'{self.name.lower()}': float(rsi_value) if not np.isnan(rsi_value) else np.nan
        }
        
        return IndicatorResult(
            name=self.name,
            values=values,
            metadata={'window': self.window}
        )
    
    @property
    def required_columns(self) -> List[str]:
        return ['close']
    
    @property
    def min_periods(self) -> int:
        return self.window


@indicator_registry.register
class MACDIndicator(TechnicalIndicator):
    """MACD (Moving Average Convergence Divergence) Indicator"""
    
    def __init__(self, 
                 fast_window: int = 12, 
                 slow_window: int = 26, 
                 signal_window: int = 9,
                 name: str = "MACD"):
        super().__init__(name)
        self.fast_window = fast_window
        self.slow_window = slow_window
        self.signal_window = signal_window
        self.calculator = MACDCalculator(
            fast_window=fast_window,
            slow_window=slow_window,
            signal_window=signal_window
        )
    
    def calculate(self, df: pd.DataFrame) -> IndicatorResult:
        close_prices = df['close']
        macd_line, signal_line, histogram = self.calculator.get_last_values(close_prices)
        
        values = {
            f'{self.name.lower()}_line': float(macd_line) if not np.isnan(macd_line) else np.nan,
            f'{self.name.lower()}_signal': float(signal_line) if not np.isnan(signal_line) else np.nan,
            f'{self.name.lower()}_histogram': float(histogram) if not np.isnan(histogram) else np.nan
        }
        
        return IndicatorResult(
            name=self.name,
            values=values,
            metadata={
                'fast_window': self.fast_window,
                'slow_window': self.slow_window,
                'signal_window': self.signal_window
            }
        )
    
    @property
    def required_columns(self) -> List[str]:
        return ['close']
    
    @property
    def min_periods(self) -> int:
        return max(self.slow_window, self.signal_window)


@indicator_registry.register
class BollingerBandsIndicator(TechnicalIndicator):
    """Bollinger Bands Indicator"""
    
    def __init__(self, 
                 window: int = 20, 
                 num_std: float = 2.0,
                 name: str = "BB"):
        super().__init__(name)
        self.window = window
        self.num_std = num_std
        self.calculator = BollingerBandsCalculator(window=window, num_std=num_std)
    
    def calculate(self, df: pd.DataFrame) -> IndicatorResult:
        close_prices = df['close']
        upper_band, middle_band, lower_band, position = self.calculator.get_last_with_position(close_prices)
        
        values = {
            f'{self.name.lower()}_upper': float(upper_band) if not np.isnan(upper_band) else np.nan,
            f'{self.name.lower()}_middle': float(middle_band) if not np.isnan(middle_band) else np.nan,
            f'{self.name.lower()}_lower': float(lower_band) if not np.isnan(lower_band) else np.nan,
            f'{self.name.lower()}_position': float(position) if not np.isnan(position) else np.nan
        }
        
        return IndicatorResult(
            name=self.name,
            values=values,
            metadata={
                'window': self.window,
                'num_std': self.num_std
            }
        )
    
    @property
    def required_columns(self) -> List[str]:
        return ['close']
    
    @property
    def min_periods(self) -> int:
        return self.window


@indicator_registry.register
class PricePositionIndicator(TechnicalIndicator):
    """Price position relative to moving average"""
    
    def __init__(self, window: int = 20, name: str = "PricePosition"):
        super().__init__(name)
        self.window = window
    
    def calculate(self, df: pd.DataFrame) -> IndicatorResult:
        if len(df) < self.window:
            return IndicatorResult(
                name=self.name,
                values={f'{self.name.lower()}': np.nan},
                metadata={'window': self.window}
            )
        
        close_prices = df['close']
        ma = close_prices.rolling(window=self.window).mean().iloc[-1]
        current_price = close_prices.iloc[-1]
        
        if not np.isnan(ma) and ma != 0:
            position = current_price / ma
        else:
            position = np.nan
        
        values = {
            f'{self.name.lower()}': float(position) if not np.isnan(position) else np.nan
        }
        
        return IndicatorResult(
            name=self.name,
            values=values,
            metadata={'window': self.window}
        )
    
    @property
    def required_columns(self) -> List[str]:
        return ['close']
    
    @property
    def min_periods(self) -> int:
        return self.window


@indicator_registry.register
class VolatilityIndicator(TechnicalIndicator):
    """Price volatility indicator"""
    
    def __init__(self, window: int = 24, name: str = "Volatility"):
        super().__init__(name)
        self.window = window
    
    def calculate(self, df: pd.DataFrame) -> IndicatorResult:
        if len(df) < self.window:
            return IndicatorResult(
                name=self.name,
                values={f'{self.name.lower()}': np.nan},
                metadata={'window': self.window}
            )
        
        close_prices = df['close']
        returns = close_prices.pct_change().dropna()
        
        if len(returns) >= self.window:
            volatility = returns.tail(self.window).std() * np.sqrt(252)  # Annualized
        else:
            volatility = np.nan
        
        values = {
            f'{self.name.lower()}': float(volatility) if not np.isnan(volatility) else np.nan
        }
        
        return IndicatorResult(
            name=self.name,
            values=values,
            metadata={'window': self.window}
        )
    
    @property
    def required_columns(self) -> List[str]:
        return ['close']
    
    @property
    def min_periods(self) -> int:
        return self.window