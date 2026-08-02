import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from regime.regime_labeler import RegimeLabeler
from regime.regime_types import MarketRegime


class TestRegimeLabeler:
    def setup_method(self):
        self.labeler = RegimeLabeler()

    def test_trend_up(self):
        feature = {
            "adx_4h": 30,
            "plus_di_4h": 28,
            "minus_di_4h": 15,
            "trend_continuation_4h": 0.5,
            "ema_cross_4h_12_26": 1,
            "atr_ratio_4h_1h": 2.8,
            "macd_histogram_4h": 0.5,
            "ema_12_4h": 0.2,
            "ema_26_4h": -0.1,
        }
        assert self.labeler.classify(feature) == int(MarketRegime.TREND_UP)

    def test_trend_down(self):
        feature = {
            "adx_4h": 32,
            "plus_di_4h": 12,
            "minus_di_4h": 30,
            "trend_continuation_4h": -0.6,
            "ema_cross_4h_12_26": -1,
            "atr_ratio_4h_1h": 2.5,
            "macd_histogram_4h": -0.4,
            "ema_12_4h": -0.2,
            "ema_26_4h": 0.1,
        }
        assert self.labeler.classify(feature) == int(MarketRegime.TREND_DOWN)

    def test_range_low_adx(self):
        feature = {
            "adx_4h": 15,
            "plus_di_4h": 20,
            "minus_di_4h": 18,
            "trend_continuation_4h": 0.05,
            "ema_cross_4h_12_26": 0,
            "atr_ratio_4h_1h": 2.5,
            "macd_histogram_4h": 0,
            "ema_12_4h": 0,
            "ema_26_4h": 0,
        }
        assert self.labeler.classify(feature) == int(MarketRegime.RANGE)

    def test_range_low_atr_ratio(self):
        # Cross-TF: ATR(4H)/ATR(1H) below √4≈2 → 1H noise dominates → RANGE
        feature = {
            "adx_4h": 25,
            "plus_di_4h": 22,
            "minus_di_4h": 20,
            "trend_continuation_4h": 0.3,
            "ema_cross_4h_12_26": 1,
            "atr_ratio_4h_1h": 1.5,
            "macd_histogram_4h": 0.2,
            "ema_12_4h": 0.1,
            "ema_26_4h": 0,
        }
        assert self.labeler.classify(feature) == int(MarketRegime.RANGE)

    def test_confirmed_change_requires_consecutive_rows(self):
        up = {
            "adx_4h": 30,
            "plus_di_4h": 30,
            "minus_di_4h": 10,
            "trend_continuation_4h": 0.5,
            "ema_cross_4h_12_26": 1,
            "atr_ratio_4h_1h": 2.5,
            "macd_histogram_4h": 1,
            "ema_12_4h": 1,
            "ema_26_4h": 0,
        }
        down = {
            **up,
            "plus_di_4h": 10,
            "minus_di_4h": 30,
            "trend_continuation_4h": -0.5,
            "ema_cross_4h_12_26": -1,
            "macd_histogram_4h": -1,
            "ema_12_4h": -1,
            "ema_26_4h": 0,
        }
        changed, first_hour = self.labeler._confirmed_change(
            int(MarketRegime.TREND_UP), [down, up, down]
        )
        assert changed == 0
        assert first_hour is None

        changed, first_hour = self.labeler._confirmed_change(
            int(MarketRegime.TREND_UP), [up, down, down]
        )
        assert changed == 1
        assert first_hour == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
