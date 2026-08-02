"""Synthetic end-to-end test for purged CV, calibration and model metadata."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from models import regime_trainer as trainer_module  # noqa: E402
from models.regime_trainer import REGIME_FEATURE_COLUMNS, RegimeTrainer  # noqa: E402


def test_walkforward_training_and_reload(monkeypatch, tmp_path):
    rows = []
    for i in range(700):
        # Predictable but nontrivial transition signal with both classes in every fold.
        change = int((i % 10) >= 6)
        row = {column: 0.0 for column in REGIME_FEATURE_COLUMNS}
        row.update(
            {
                "timestamp": 1_700_000_000_000 + i * 3_600_000,
                "inst_id": "ETH-USDT-SWAP",
                "bar": "1H",
                "regime_now": 3,
                "regime_48h": 1 if change else 3,
                "regime_horizon_hours": 12,
                "transition_confirm_bars": 2,
                "transition_confirmed_change": change,
                "feature_schema_version": "transition_v1",
                "dynamic_features_ready": True,
                "price_return_1h": 0.05 if change else -0.02,
                "adx_4h_delta_6h": 2.0 if change else -1.0,
            }
        )
        rows.append(row)

    monkeypatch.setattr(
        trainer_module.feature_handler,
        "get_features_for_regime",
        lambda **_kwargs: rows,
    )
    model_path = tmp_path / "transition.json"
    trainer = RegimeTrainer(str(model_path))
    result = trainer.train_model(
        limit=700,
        test_ratio=0.2,
        class_weight="none",
        horizon_hours=12,
        holdout_start_ts=rows[560]["timestamp"],
    )

    assert result["target"] == "continue_change"
    assert result["purge_rows"] == 12
    assert result["holdout_start_ts"] == rows[560]["timestamp"]
    assert len(result["walk_forward"]["candidate_modes"]["none"]["folds"]) >= 2
    assert "pr_auc" in result
    assert "RANGE" in result["regime_policies"]
    assert model_path.exists()
    assert (tmp_path / "transition_calibrator.pkl").exists()

    loaded = RegimeTrainer(str(model_path))
    assert loaded.load_model() is True
    assert loaded.horizon_hours == 12
    assert loaded.label_version == "confirmed_change_v1"
    assert "RANGE" in loaded.regime_policies

    meta_path = tmp_path / "transition_meta.json"
    meta = json.loads(meta_path.read_text())
    meta["label_version"] = "endpoint_change_legacy"
    meta_path.write_text(json.dumps(meta))
    assert RegimeTrainer(str(model_path)).load_model() is False
