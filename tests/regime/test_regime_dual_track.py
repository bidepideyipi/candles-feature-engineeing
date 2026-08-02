"""Continue/change trainer helpers + prediction payload."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from models.regime_trainer import (  # noqa: E402
    CHANGE,
    CONTINUE,
    RegimeTrainer,
)
from regime.regime_types import MarketRegime  # noqa: E402


def test_present_series_requires_regime_now():
    trainer = RegimeTrainer.__new__(RegimeTrainer)
    df = pd.DataFrame({"regime_now": [1, 2, 3]})
    s = trainer._present_series(df)
    assert list(s.astype(int)) == [1, 2, 3]


def test_balanced_sample_weights_named_continue_change():
    trainer = RegimeTrainer.__new__(RegimeTrainer)
    y = pd.Series([0, 0, 0, 0, 0, 1, 1])  # continue majority
    sw, named = trainer._balanced_sample_weights(y)
    assert "CONTINUE" in named and "CHANGE" in named
    assert named["CHANGE"] > named["CONTINUE"]
    assert abs(sw[-1] - named["CHANGE"]) < 1e-3


def test_build_prediction_payload_transition(monkeypatch):
    trainer = RegimeTrainer.__new__(RegimeTrainer)
    trainer.feature_columns = ["adx_4h"]
    trainer.horizon_hours = 6
    trainer.class_weight_mode = "balanced"
    trainer.change_threshold = 0.5
    trainer.target = "continue_change"
    trainer.gate_passed = True
    trainer.regime_policies = {
        "RANGE": {
            "threshold": 0.65,
            "alert_enabled": True,
            "holdout_gate_reasons": {
                "change_precision": True,
                "accuracy_vs_always_continue": True,
                "pr_auc_vs_prevalence": True,
            },
        }
    }
    trainer._labeler = MagicMock()
    trainer._labeler.classify.return_value = int(MarketRegime.RANGE)
    trainer.predict_single = MagicMock(
        return_value=(CHANGE, np.array([0.3, 0.7]), "n/a", 0.7)
    )

    payload = trainer.build_prediction_payload(
        {
            "timestamp": 1_700_000_000_000,
            "inst_id": "ETH-USDT-SWAP",
            "bar": "1H",
            "price": 2500.0,
            "adx_4h": 20,
        }
    )
    assert payload["target"] == "continue_change"
    assert payload["present"]["regime"] == 3
    assert payload["transition"]["changes"] is True
    assert payload["transition"]["p_change"] == 0.7
    assert payload["transition"]["threshold"] == 0.65
    assert payload["transition"]["alert_eligible"] is True
    assert payload["derived"]["continues"] is False
    assert payload["regime"] == 3  # flat = present rules


def test_regime_policy_suppresses_weak_subgroup_alert():
    trainer = RegimeTrainer.__new__(RegimeTrainer)
    trainer.feature_columns = ["adx_4h"]
    trainer.horizon_hours = 12
    trainer.class_weight_mode = "none"
    trainer.change_threshold = 0.36
    trainer.target = "continue_change"
    trainer.gate_passed = True
    trainer.calibrator = None
    trainer.model_version = "test"
    trainer.regime_policies = {
        "TREND_DOWN": {
            "threshold": 0.7,
            "alert_enabled": False,
            "holdout_gate_reasons": {
                "change_precision": False,
                "accuracy_vs_always_continue": False,
                "pr_auc_vs_prevalence": True,
            },
        }
    }
    trainer._labeler = MagicMock()
    trainer._labeler.classify.return_value = int(MarketRegime.TREND_DOWN)
    trainer.predict_single = MagicMock(
        return_value=(CHANGE, np.array([0.2, 0.8]), "n/a", 0.8)
    )
    payload = trainer.build_prediction_payload(
        {"timestamp": 1, "adx_4h": 25}
    )
    assert payload["transition"]["changes"] is True
    assert payload["transition"]["threshold"] == 0.7
    assert payload["transition"]["model_gate_passed"] is False
    assert payload["transition"]["alert_eligible"] is False


def test_labeler_horizon_from_arg():
    from regime.regime_labeler import RegimeLabeler

    assert RegimeLabeler(horizon_hours=12).horizon_hours == 12
    assert RegimeLabeler(horizon_hours=12).horizon_ms == 12 * 3600 * 1000


def test_purged_walk_forward_has_horizon_gap():
    splits = RegimeTrainer._walk_forward_splits(
        n_rows=1000, holdout_start=800, horizon_rows=12, n_splits=3
    )
    assert len(splits) == 3
    for train_idx, val_idx in splits:
        assert val_idx[0] - train_idx[-1] - 1 >= 12
        assert train_idx[-1] < val_idx[0]


def test_timestamp_purge_handles_irregular_rows():
    # Row indexes are not a safe proxy when hours are missing.
    timestamps = np.array(
        [1_700_000_000_000 + i * 3_600_000 for i in range(1000)],
        dtype=np.int64,
    )
    timestamps[400:] += 5 * 3_600_000
    splits = RegimeTrainer._walk_forward_splits(
        n_rows=1000,
        holdout_start=800,
        horizon_rows=12,
        n_splits=3,
        timestamps=timestamps,
    )
    for train_idx, val_idx in splits:
        assert (
            timestamps[train_idx[-1]] + 12 * 3_600_000
            < timestamps[val_idx[0]]
        )


def test_threshold_sweep_requires_precision_and_baseline_gain():
    y = np.array([0, 0, 0, 0, 1, 1])
    p = np.array([0.05, 0.1, 0.2, 0.8, 0.7, 0.9])
    threshold, rows = RegimeTrainer._threshold_sweep(y, p, min_precision=0.5)
    selected = next(row for row in rows if row["threshold"] == threshold)
    assert selected["precision"] > 0.5
    assert selected["accuracy_gain_vs_continue"] > 0


def test_platt_calibration_outputs_probabilities():
    raw = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])
    y = np.array([0, 0, 0, 1, 1, 1])
    calibrator = RegimeTrainer._fit_calibrator(raw, y)
    calibrated = RegimeTrainer._apply_calibrator(raw, calibrator)
    assert np.all((calibrated > 0) & (calibrated < 1))
    assert calibrated[-1] > calibrated[0]
