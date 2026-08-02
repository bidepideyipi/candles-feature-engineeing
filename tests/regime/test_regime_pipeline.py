import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from collect.candlestick_continuity import (
    BAR_INTERVAL_MS,
    CandlestickContinuityChecker,
)
from regime.regime_pipeline import RegimePipeline


class TestCandlestickContinuity:
    def setup_method(self):
        self.checker = CandlestickContinuityChecker()

    def test_continuous_1h(self):
        interval = BAR_INTERVAL_MS["1H"]
        base = 1_700_000_000_000
        timestamps = [base + i * interval for i in range(10)]

        with patch.object(self.checker, "_load_timestamps", return_value=timestamps):
            result = self.checker.check_bar("ETH-USDT-SWAP", "1H")

        assert result["ok"] is True
        assert result["gap_count"] == 0
        assert result["count"] == 10

    def test_gap_detected(self):
        interval = BAR_INTERVAL_MS["1H"]
        base = 1_700_000_000_000
        # skip index 5 → one gap of 1 missing bar
        timestamps = [base + i * interval for i in range(10) if i != 5]

        with patch.object(self.checker, "_load_timestamps", return_value=timestamps):
            result = self.checker.check_bar("ETH-USDT-SWAP", "1H")

        assert result["ok"] is False
        assert result["gap_count"] == 1
        assert result["missing_bars_estimate"] == 1
        assert result["gaps"][0]["missing_bars"] == 1

    def test_empty(self):
        with patch.object(self.checker, "_load_timestamps", return_value=[]):
            result = self.checker.check_bar("ETH-USDT-SWAP", "4H")
        assert result["ok"] is False
        assert result["error"] == "无数据"


class TestRegimePipelinePlan:
    def test_plan_pull_counts_scales_from_1h(self):
        pipeline = RegimePipeline()
        targets = pipeline._plan_pull_counts(2400, ["15m", "1H", "4H", "1D"])
        assert targets["1H"] == 2400
        assert targets["15m"] == 9600
        assert targets["4H"] == 600
        assert targets["1D"] == 100

    def test_plan_clamps_to_max(self):
        pipeline = RegimePipeline()
        targets = pipeline._plan_pull_counts(10000, ["15m", "1H"])
        assert targets["1H"] == 10000
        assert targets["15m"] == 10000  # 40000 clamped

    def test_run_stops_on_continuity_failure(self):
        pipeline = RegimePipeline()
        continuity_fail = {
            "ok": False,
            "failed_bars": ["1H"],
            "message": "不连续: 1H",
            "bars": {},
        }
        with patch.object(
            pipeline,
            "_step_pull",
            return_value={"success": True, "counts": {}, "skipped": False},
        ), patch(
            "regime.regime_pipeline.candlestick_continuity_checker.check_all",
            return_value=continuity_fail,
        ):
            report = pipeline.run(
                skip_pull=False,
                strict_continuity=True,
                max_records_1h=500,
            )

        assert report["success"] is False
        assert report["failed_step"] == "continuity"
        assert "summary" in report
        assert report["steps"]["continuity"]["ok"] is False

    def test_build_summary_shape(self):
        pipeline = RegimePipeline()
        with patch.object(
            pipeline, "_candle_counts", return_value={"1H": 100, "4H": 25}
        ):
            summary = pipeline._build_summary(
                inst_id="ETH-USDT-SWAP",
                bars=["1H", "4H"],
                continuity={"ok": True, "failed_bars": []},
                merge_result={"processed": 50, "features_in_db": 50},
                label_result={
                    "labeled_after": 50,
                    "regime_distribution": {"RANGE": 30, "TREND_UP": 20},
                },
                train_result={
                    "accuracy": 0.8,
                    "train_size": 40,
                    "test_size": 10,
                    "test_period": {"from_ts": 1, "to_ts": 2},
                    "feature_columns": ["a", "b"],
                    "classification_report": {
                        "CHANGE": {
                            "precision": 0.7,
                            "recall": 0.8,
                            "f1-score": 0.75,
                            "support": 5,
                        },
                        "macro avg": {"f1-score": 0.7},
                        "weighted avg": {"f1-score": 0.72},
                    },
                    "confusion_matrix": [[1, 0], [0, 1]],
                    "trained_at": "2026-01-01T00:00:00",
                },
            )

        assert summary["accuracy"] == 0.8
        assert summary["continuity_ok"] is True
        assert summary["regime_distribution"]["RANGE"] == 30
        assert summary["per_class"]["CHANGE"]["f1"] == 0.75
        assert summary["macro_f1"] == 0.7
