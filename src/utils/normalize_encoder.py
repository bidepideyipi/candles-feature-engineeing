"""
Normalized Price Calculator
Supports rolling-window and legacy global normalization.
"""

import pandas as pd
from typing import Tuple, Union

from .calculator_interface import BaseTechnicalCalculator


class Normalized(BaseTechnicalCalculator):
    """Price/volume normalization with rolling or global window."""

    def calculate_rolling(
        self,
        prices: Union[pd.Series, list],
        window: int = 168,
    ) -> Tuple[float, float, float]:
        """
        Rolling normalization: mean/std over the last `window` bars,
        normalize the latest value.

        Returns:
            (normalized_last, mean, std)
        """
        prices_series = self._convert_to_series(prices)
        if len(prices_series) == 0:
            raise ValueError("Cannot calculate normalization: input data is empty")

        slice_ = (
            prices_series.iloc[-window:]
            if len(prices_series) >= window
            else prices_series
        )
        rolling_mean = float(slice_.mean())
        rolling_std = float(slice_.std())

        if pd.isna(rolling_std) or rolling_std == 0:
            raise ValueError(
                f"Cannot calculate rolling normalization: std={rolling_std}, mean={rolling_mean}"
            )

        last = float(prices_series.iloc[-1])
        normalized = (last - rolling_mean) / rolling_std
        return float(normalized), rolling_mean, rolling_std

    def calculate(
        self, close_prices: Union[pd.Series, list]
    ) -> Tuple[float, float, float]:
        """
        Legacy global normalization over the entire series.
        Deprecated: use calculate_rolling() in feature pipeline.
        """
        prices_series = self._convert_to_series(close_prices)
        if len(prices_series) == 0:
            raise ValueError("Cannot calculate normalization: input data is empty")

        rolling_mean = float(prices_series.mean())
        rolling_std = float(prices_series.std())

        if pd.isna(rolling_std) or rolling_std == 0:
            raise ValueError(
                f"Cannot calculate normalization: std={rolling_std}, mean={rolling_mean}"
            )

        normalized = (prices_series - rolling_mean) / rolling_std
        return float(normalized.iloc[-1]), rolling_mean, rolling_std


NORMALIZED = Normalized()
