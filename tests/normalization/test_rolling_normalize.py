"""Tests for rolling normalization."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.normalize_encoder import NORMALIZED


def test_rolling_uses_last_window_only():
    # 前 100 根低价 + 后 68 根高价 → 全局 mean 会偏低，rolling 168 应反映近期高价
    prices = [100.0] * 100 + [200.0] * 68
    norm_global, mean_g, _ = NORMALIZED.calculate(prices)
    norm_roll, mean_r, std_r = NORMALIZED.calculate_rolling(prices, window=168)

    assert mean_r > mean_g, "rolling mean should weight recent high prices more"
    assert abs(norm_roll) < 5, "normalized value should be reasonable"
    assert std_r > 0


def test_rolling_short_series():
    prices = [100.0, 101.0, 102.0, 99.0, 100.5]
    norm, mean, std = NORMALIZED.calculate_rolling(prices, window=168)
    assert std > 0
    assert -5 < norm < 5


if __name__ == "__main__":
    test_rolling_uses_last_window_only()
    test_rolling_short_series()
    print("rolling normalization tests OK")
