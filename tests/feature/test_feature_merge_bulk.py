"""Unit tests for FeatureMerge bulk window helpers (no Mongo)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from feature.feature_merge import FeatureMerge, MS_1H  # noqa: E402
from feature.feature_types import Feature  # noqa: E402


def test_window_before_takes_last_n():
    series = [{"timestamp": i * MS_1H, "v": i} for i in range(10)]
    ts = [r["timestamp"] for r in series]
    out = FeatureMerge._window_before(series, ts, before_excl=7 * MS_1H, n=3)
    assert [r["v"] for r in out] == [4, 5, 6]


def test_window_before_clamps_start():
    series = [{"timestamp": i * MS_1H} for i in range(3)]
    ts = [r["timestamp"] for r in series]
    out = FeatureMerge._window_before(series, ts, before_excl=10 * MS_1H, n=100)
    assert len(out) == 3


def test_transition_enrichment_is_deterministic_for_same_history():
    history = [
        {
            "timestamp": i * MS_1H,
            "price": 100 + i,
            "adx_4h": 18 + i / 10,
            "plus_di_4h": 25,
            "minus_di_4h": 20,
            "macd_histogram_4h": i / 100,
            "ema_12_4h": 1.0,
            "ema_26_4h": 0.5,
            "atr_ratio_4h_1h": 2.2,
            "rsi_14_1h": 50 + i / 10,
            "bollinger_position_1d": 0.5,
            "trend_continuation_4h": 0.2,
            "ema_cross_4h_12_26": 1,
        }
        for i in range(24)
    ]
    base = dict(
        timestamp=24 * MS_1H,
        price=125,
        adx_4h=22,
        plus_di_4h=27,
        minus_di_4h=19,
        macd_histogram_4h=0.4,
        ema_12_4h=1.2,
        ema_26_4h=0.4,
        atr_ratio_4h_1h=2.4,
        rsi_14_1h=55,
        bollinger_position_1d=0.7,
        trend_continuation_4h=0.3,
        ema_cross_4h_12_26=1,
    )
    fm = FeatureMerge()
    a = fm._enrich_transition_features(Feature(**base), history).to_dict()
    b = fm._enrich_transition_features(Feature(**base), history).to_dict()
    keys = [
        "price_return_4h",
        "adx_4h_delta_6h",
        "ema_gap_4h_delta_6h",
        "regime_age_1h",
        "regime_switches_24h",
    ]
    assert {k: a[k] for k in keys} == {k: b[k] for k in keys}
