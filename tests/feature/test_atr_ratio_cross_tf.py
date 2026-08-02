"""Cross-timeframe atr_ratio_* = ATR(higher)/ATR(lower)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from feature.feature_1h_creator import Feature1HCreator  # noqa: E402
from feature.feature_4h_creator import Feature4HCreator  # noqa: E402
from utils.atr_calculator import ATR_CALCULATOR  # noqa: E402
from utils.atr_ratio_calculator import ATR_RATIO_CALCULATOR  # noqa: E402


def _ohlc(n: int, base: float = 100.0, vol: float = 1.0, seed: int = 0):
    rng = np.random.default_rng(seed)
    rows = []
    price = base
    for i in range(n):
        noise = float(rng.normal(0, vol))
        o, c = price, price + noise
        h, l = max(o, c) + abs(vol), min(o, c) - abs(vol)
        rows.append(
            {
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "volume": 1000,
                "timestamp": i * 3_600_000,
                "record_hour": i % 24,
                "day_of_week": i % 7,
            }
        )
        price = c
    return rows


def test_cross_timeframe_ratio_is_atr_num_over_den():
    df_4h = pd.DataFrame(_ohlc(48, vol=4.0, seed=1))
    df_1h = pd.DataFrame(_ohlc(48, vol=1.0, seed=2))
    ratio = ATR_RATIO_CALCULATOR.calculate_cross_timeframe_ratio(df_4h, df_1h)
    expected = ATR_CALCULATOR.calculate(df_4h) / ATR_CALCULATOR.calculate(df_1h)
    assert abs(ratio - expected) < 1e-9
    assert ratio > 1.0


def test_feature_creators_use_cross_tf_ratios():
    c1h = _ohlc(48, vol=1.0, seed=3)
    c15 = _ohlc(48, vol=0.4, seed=4)
    c4h = _ohlc(48, vol=3.0, seed=5)

    f1 = Feature1HCreator(0.0, 1.0, 0.0, 1.0).calculate(c1h, c15)
    f4 = Feature4HCreator(0.0, 1.0).calculate(c4h, c1h)

    assert f1.atr_ratio_1h_15m > 0
    assert f4.atr_ratio_4h_1h > 0

    df_1h = pd.DataFrame(c1h)[["high", "low", "close"]]
    df_15 = pd.DataFrame(c15)[["high", "low", "close"]]
    df_4h = pd.DataFrame(c4h)[["high", "low", "close"]]
    assert abs(
        f1.atr_ratio_1h_15m
        - round(ATR_RATIO_CALCULATOR.calculate_cross_timeframe_ratio(df_1h, df_15), 2)
    ) < 1e-9
    assert abs(
        f4.atr_ratio_4h_1h
        - round(ATR_RATIO_CALCULATOR.calculate_cross_timeframe_ratio(df_4h, df_1h), 2)
    ) < 1e-9
