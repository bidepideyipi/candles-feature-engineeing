"""
XGBoost binary: will present regime continue or change over the horizon?

Target (from dual labels already in Mongo):
  change    = 1  if regime_48h != regime_now
  continue  = 0  if regime_48h == regime_now

Present structure stays rule-based. Model only answers transition risk.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
    precision_score,
    roc_auc_score,
)
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_class_weight

from collect.feature_handler import feature_handler
from config.settings import config
from feature.feature_types import Feature
from regime.regime_labeler import RegimeLabeler
from regime.regime_types import (
    REGIME_DESCRIPTION,
    REGIME_HORIZON_HOURS_DEFAULT,
    REGIME_LABELS,
    REGIME_STRATEGY,
    MarketRegime,
)

logger = logging.getLogger(__name__)

REGIME_FEATURE_COLUMNS = [
    "adx_4h", "plus_di_4h", "minus_di_4h", "trend_continuation_4h",
    "ema_12_4h", "ema_26_4h", "ema_48_4h",
    "ema_cross_4h_12_26", "ema_cross_4h_26_48",
    "atr_4h", "atr_ratio_4h_1h", "rsi_14_4h", "rsi_divergence_4h",
    "macd_histogram_4h", "macd_line_4h", "macd_signal_4h",
    "adx_1h", "plus_di_1h", "minus_di_1h", "atr_ratio_1h_15m", "rsi_14_1h",
    "atr_15m", "rsi_14_15m", "stoch_k_15m", "stoch_d_15m",
    "bollinger_position_1d", "atr_1d", "rsi_14_1d",
    "price_return_1h", "price_return_4h", "price_return_12h",
    "adx_4h_delta_3h", "adx_4h_delta_6h", "adx_4h_delta_12h",
    "di_spread_4h", "di_spread_4h_delta_6h",
    "macd_histogram_4h_delta_6h",
    "ema_gap_4h", "ema_gap_4h_delta_6h",
    "atr_ratio_4h_1h_delta_6h", "rsi_14_1h_delta_6h",
    "bollinger_position_1d_delta_12h",
    "adx_range_margin", "adx_trend_margin", "atr_ratio_range_margin",
    "regime_age_1h", "regime_switches_24h", "rule_conflict_score",
]

TRANSITION_DYNAMIC_COLUMNS = [
    "price_return_1h", "price_return_4h", "price_return_12h",
    "adx_4h_delta_3h", "adx_4h_delta_6h", "adx_4h_delta_12h",
    "di_spread_4h", "di_spread_4h_delta_6h",
    "macd_histogram_4h_delta_6h", "ema_gap_4h",
    "ema_gap_4h_delta_6h", "atr_ratio_4h_1h_delta_6h",
    "rsi_14_1h_delta_6h", "bollinger_position_1d_delta_12h",
    "adx_range_margin", "adx_trend_margin", "atr_ratio_range_margin",
    "regime_age_1h", "regime_switches_24h", "rule_conflict_score",
]

# Binary labels
CONTINUE = 0
CHANGE = 1
TRANSITION_NAMES = {CONTINUE: "CONTINUE", CHANGE: "CHANGE"}


class RegimeTrainer:
    """Train/load continue-vs-change model at configurable horizon."""

    def __init__(self, model_save_path: str = None):
        self.model_save_path = model_save_path or config.REGIME_MODEL_SAVE_PATH
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns: Optional[List[str]] = None
        self._labeler = RegimeLabeler()
        self.horizon_hours = int(
            getattr(config, "REGIME_HORIZON_HOURS", REGIME_HORIZON_HOURS_DEFAULT)
        )
        self.class_weight_mode = getattr(config, "REGIME_CLASS_WEIGHT", "balanced")
        self.target = "continue_change"
        self.change_threshold = float(
            getattr(config, "REGIME_CHANGE_THRESHOLD", 0.5)
        )
        self.calibrator: Optional[LogisticRegression] = None
        self.gate_passed = False
        self.label_version = "confirmed_change_v1"
        self.validation_summary: Dict[str, Any] = {}
        self.gate_reasons: Dict[str, bool] = {}
        self.model_version = "untrained"
        self.regime_policies: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _present_series(df: pd.DataFrame) -> pd.Series:
        if "regime_now" not in df.columns:
            raise ValueError("missing regime_now for continue/change labels")
        return df["regime_now"]

    @staticmethod
    def _balanced_sample_weights(y: pd.Series) -> Tuple[np.ndarray, Dict[str, float]]:
        y_arr = y.to_numpy()
        classes = np.unique(y_arr)
        weights = compute_class_weight(
            class_weight="balanced", classes=classes, y=y_arr
        )
        weight_map = {int(c): float(w) for c, w in zip(classes, weights)}
        sample_weight = np.array([weight_map[int(c)] for c in y_arr], dtype=float)
        named = {
            TRANSITION_NAMES.get(i, str(i)): round(weight_map[i], 4)
            for i in sorted(weight_map)
        }
        return sample_weight, named

    @staticmethod
    def _walk_forward_splits(
        n_rows: int,
        holdout_start: int,
        horizon_rows: int,
        n_splits: int,
        timestamps: Optional[np.ndarray] = None,
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Expanding walk-forward folds with a purged label gap."""
        if holdout_start < 300:
            raise ValueError("insufficient development rows for walk-forward")
        n_splits = max(2, int(n_splits))
        val_size = max(100, holdout_start // (n_splits + 2))
        splits: List[Tuple[np.ndarray, np.ndarray]] = []
        first_val_start = holdout_start - val_size * n_splits
        for fold in range(n_splits):
            val_start = first_val_start + fold * val_size
            val_end = min(holdout_start, val_start + val_size)
            if timestamps is not None:
                validation_start_ts = int(timestamps[val_start])
                horizon_ms = max(1, horizon_rows) * 60 * 60 * 1000
                train_idx = np.flatnonzero(
                    timestamps[:val_start] + horizon_ms < validation_start_ts
                )
            else:
                train_end = val_start - max(1, horizon_rows)
                train_idx = np.arange(0, max(0, train_end), dtype=int)
            if len(train_idx) < 100 or val_end <= val_start:
                continue
            splits.append(
                (
                    train_idx,
                    np.arange(val_start, val_end, dtype=int),
                )
            )
        if len(splits) < 2:
            raise ValueError("unable to build at least two purged walk-forward folds")
        return splits

    def _fit_booster(
        self,
        X_train: np.ndarray,
        y_train: pd.Series,
        weight_mode: str,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[pd.Series] = None,
    ) -> Tuple[xgb.Booster, Dict[str, float]]:
        sample_weight = None
        class_weights: Dict[str, float] = {}
        if weight_mode == "balanced":
            sample_weight, class_weights = self._balanced_sample_weights(y_train)
        dtrain = xgb.DMatrix(X_train, label=y_train, weight=sample_weight)
        params = {
            "objective": "binary:logistic",
            "max_depth": 6,
            "learning_rate": 0.05,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "min_child_weight": 5,
            "gamma": 0.1,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
            "random_state": 42,
            "eval_metric": "logloss",
        }
        evals = [(dtrain, "train")]
        kwargs: Dict[str, Any] = {}
        if X_val is not None and y_val is not None:
            dval = xgb.DMatrix(X_val, label=y_val)
            evals.append((dval, "validation"))
            kwargs["early_stopping_rounds"] = 15
        model = xgb.train(
            params,
            dtrain,
            num_boost_round=150,
            evals=evals,
            verbose_eval=False,
            **kwargs,
        )
        return model, class_weights

    @staticmethod
    def _fit_calibrator(
        raw_prob: np.ndarray, y_true: np.ndarray
    ) -> Optional[LogisticRegression]:
        if len(np.unique(y_true)) < 2:
            return None
        calibrator = LogisticRegression(random_state=42)
        calibrator.fit(raw_prob.reshape(-1, 1), y_true)
        return calibrator

    @staticmethod
    def _apply_calibrator(
        raw_prob: np.ndarray, calibrator: Optional[LogisticRegression]
    ) -> np.ndarray:
        clipped = np.clip(np.asarray(raw_prob, dtype=float), 1e-6, 1 - 1e-6)
        if calibrator is None:
            return clipped
        return calibrator.predict_proba(clipped.reshape(-1, 1))[:, 1]

    @staticmethod
    def _threshold_sweep(
        y_true: np.ndarray,
        probabilities: np.ndarray,
        min_precision: float,
    ) -> Tuple[float, List[Dict[str, Any]]]:
        rows: List[Dict[str, Any]] = []
        baseline = float(np.mean(y_true == CONTINUE))
        for threshold in np.arange(0.30, 0.901, 0.02):
            pred = (probabilities >= threshold).astype(int)
            precision = float(precision_score(y_true, pred, zero_division=0))
            recall = float(
                np.sum((pred == CHANGE) & (y_true == CHANGE))
                / max(1, np.sum(y_true == CHANGE))
            )
            accuracy = float(accuracy_score(y_true, pred))
            alert_rate = float(np.mean(pred == CHANGE))
            f1 = (
                2 * precision * recall / (precision + recall)
                if precision + recall
                else 0.0
            )
            rows.append(
                {
                    "threshold": round(float(threshold), 2),
                    "precision": round(precision, 4),
                    "recall": round(recall, 4),
                    "f1": round(f1, 4),
                    "accuracy": round(accuracy, 4),
                    "alert_rate": round(alert_rate, 4),
                    "accuracy_gain_vs_continue": round(accuracy - baseline, 4),
                }
            )
        eligible = [
            row
            for row in rows
            if row["precision"] > min_precision
            and row["accuracy_gain_vs_continue"] > 0
        ]
        pool = eligible or rows
        best = max(pool, key=lambda row: (row["f1"], row["accuracy"]))
        return float(best["threshold"]), rows

    @staticmethod
    def _binary_metrics(
        y_true: np.ndarray,
        probability: np.ndarray,
        threshold: Union[float, np.ndarray],
    ) -> Dict[str, Any]:
        pred = (probability >= threshold).astype(int)
        prevalence = float(np.mean(y_true == CHANGE))
        always_continue = float(np.mean(y_true == CONTINUE))
        change_precision = float(
            precision_score(y_true, pred, pos_label=CHANGE, zero_division=0)
        )
        try:
            roc_auc = float(roc_auc_score(y_true, probability))
        except ValueError:
            roc_auc = None
        try:
            pr_auc = float(average_precision_score(y_true, probability))
        except ValueError:
            pr_auc = None
        return {
            "accuracy": float(accuracy_score(y_true, pred)),
            "always_continue_baseline": always_continue,
            "always_change_baseline": prevalence,
            "majority_baseline_accuracy": max(always_continue, prevalence),
            "roc_auc": roc_auc,
            "pr_auc": pr_auc,
            "brier_score": float(brier_score_loss(y_true, probability)),
            "change_precision": change_precision,
            "predicted_change_rate": float(np.mean(pred == CHANGE)),
            "test_change_rate": prevalence,
            "classification_report": classification_report(
                y_true,
                pred,
                labels=[CONTINUE, CHANGE],
                target_names=["CONTINUE", "CHANGE"],
                output_dict=True,
                zero_division=0,
            ),
            "confusion_matrix": confusion_matrix(
                y_true, pred, labels=[CONTINUE, CHANGE]
            ).tolist(),
        }

    def train_model(
        self,
        inst_id: str = "ETH-USDT-SWAP",
        bar: str = "1H",
        limit: int = 10000,
        test_ratio: float = 0.2,
        class_weight: Optional[str] = None,
        horizon_hours: Optional[int] = None,
        holdout_start_ts: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Purged walk-forward train, calibrate on OOF, evaluate once on holdout.

        Horizon is taken from labeled features (`regime_horizon_hours`), not from
        env alone. Pass `horizon_hours` only to disambiguate when Mongo still
        contains multiple label horizons.
        """
        rows = feature_handler.get_features_for_regime(
            inst_id=inst_id,
            bar=bar,
            limit=limit,
            # Do not pre-filter by caller/env horizon; resolve from labels.
            horizon_hours=None,
            confirm_bars=getattr(config, "REGIME_CHANGE_CONFIRM_BARS", 2),
        )
        if not rows or len(rows) < 500:
            raise ValueError(
                f"confirmed transition samples insufficient: {len(rows) if rows else 0}"
            )
        df = pd.DataFrame(rows).dropna(
            subset=[
                "regime_now",
                "transition_confirmed_change",
                "regime_horizon_hours",
            ]
        )
        horizons = sorted(
            {int(h) for h in df["regime_horizon_hours"].astype(int).tolist()}
        )
        if not horizons:
            raise ValueError(
                "no regime_horizon_hours on labeled features; "
                "run /regime/1-label?only_fix_none=false"
            )
        if horizon_hours is not None:
            requested = int(horizon_hours)
            if requested not in horizons:
                raise ValueError(
                    f"requested horizon_hours={requested} not found in labels "
                    f"(available={horizons}); re-run /regime/1-label first"
                )
            if len(horizons) > 1:
                logger.warning(
                    "Multiple label horizons %s in training window; "
                    "using explicit horizon_hours=%s",
                    horizons,
                    requested,
                )
            self.horizon_hours = requested
        elif len(horizons) == 1:
            self.horizon_hours = int(horizons[0])
        else:
            raise ValueError(
                f"labeled features contain multiple horizons {horizons}; "
                "re-run /regime/1-label?only_fix_none=false with one horizon, "
                "or pass horizon_hours to select one"
            )
        self._labeler = RegimeLabeler(horizon_hours=self.horizon_hours)
        df = df[
            df["regime_horizon_hours"].astype(int) == self.horizon_hours
        ].sort_values("timestamp").reset_index(drop=True)
        if len(df) < 500:
            raise ValueError(
                f"insufficient labels for horizon={self.horizon_hours} "
                f"({len(df)} rows); re-run /regime/1-label?only_fix_none=false"
            )

        if (
            "feature_schema_version" not in df.columns
            or "dynamic_features_ready" not in df.columns
            or not (df["feature_schema_version"] == "transition_v1").all()
            or not df["dynamic_features_ready"].fillna(False).all()
        ):
            raise ValueError(
                "transition features are incomplete or use a stale schema; "
                "re-run /regime/merge-features"
            )

        target = df["transition_confirmed_change"].astype(int)
        stale = [
            column
            for column in TRANSITION_DYNAMIC_COLUMNS
            if column not in df.columns or df[column].notna().mean() < 0.95
        ]
        if stale:
            raise ValueError(
                "transition feature schema is stale; run /regime/merge-features "
                f"before training. Missing/low coverage: {stale}"
            )
        available = [c for c in REGIME_FEATURE_COLUMNS if c in df.columns]
        if not available:
            raise ValueError("no transition feature columns available")
        self.feature_columns = available
        X_df = df[available].ffill().fillna(0)

        fixed_holdout_ts = int(
            holdout_start_ts
            if holdout_start_ts is not None
            else getattr(config, "REGIME_HOLDOUT_START_TS", 0)
        )
        if fixed_holdout_ts > 0:
            holdout_start = int(
                np.searchsorted(
                    df["timestamp"].astype(np.int64).to_numpy(),
                    fixed_holdout_ts,
                    side="left",
                )
            )
            if holdout_start < 300 or len(df) - holdout_start < 100:
                raise ValueError(
                    "fixed holdout_start_ts leaves insufficient train/holdout rows"
                )
        else:
            holdout_start = int(len(df) * (1 - test_ratio))
        splits = self._walk_forward_splits(
            len(df),
            holdout_start,
            self.horizon_hours,
            getattr(config, "REGIME_CV_SPLITS", 3),
            df["timestamp"].astype(np.int64).to_numpy(),
        )
        modes = (
            [class_weight.strip().lower()]
            if class_weight is not None
            else ["none", "balanced"]
        )
        if any(mode not in ("none", "balanced") for mode in modes):
            raise ValueError("class_weight must be 'balanced', 'none', or omitted")

        mode_results: Dict[str, Dict[str, Any]] = {}
        for mode in modes:
            oof_prob: List[float] = []
            oof_true: List[int] = []
            oof_present: List[int] = []
            fold_rows: List[Dict[str, Any]] = []
            for fold_no, (train_idx, val_idx) in enumerate(splits, start=1):
                y_train_fold = target.iloc[train_idx]
                y_val_fold = target.iloc[val_idx]
                if (
                    y_train_fold.nunique() < 2
                    or y_val_fold.nunique() < 2
                ):
                    fold_rows.append(
                        {
                            "fold": fold_no,
                            "train_size": len(train_idx),
                            "validation_size": len(val_idx),
                            "purge_rows": self.horizon_hours,
                            "skipped": "single_class",
                        }
                    )
                    continue
                scaler = StandardScaler()
                X_train = scaler.fit_transform(X_df.iloc[train_idx])
                X_val = scaler.transform(X_df.iloc[val_idx])
                model, _ = self._fit_booster(
                    X_train,
                    y_train_fold,
                    mode,
                    X_val,
                    y_val_fold,
                )
                prob = model.predict(xgb.DMatrix(X_val))
                y_val = y_val_fold.to_numpy()
                oof_prob.extend(prob.tolist())
                oof_true.extend(y_val.tolist())
                oof_present.extend(
                    df.iloc[val_idx]["regime_now"].astype(int).tolist()
                )
                fold_rows.append(
                    {
                        "fold": fold_no,
                        "train_size": len(train_idx),
                        "validation_size": len(val_idx),
                        "purge_rows": self.horizon_hours,
                        "roc_auc": round(float(roc_auc_score(y_val, prob)), 4),
                        "pr_auc": round(
                            float(average_precision_score(y_val, prob)), 4
                        ),
                    }
                )
            if not oof_prob or len(set(oof_true)) < 2:
                raise ValueError(
                    f"walk-forward produced no usable two-class folds for {mode}"
                )
            raw = np.asarray(oof_prob)
            truth = np.asarray(oof_true, dtype=int)
            calibrator = self._fit_calibrator(raw, truth)
            calibrated = self._apply_calibrator(raw, calibrator)
            mode_results[mode] = {
                "pr_auc": float(average_precision_score(truth, calibrated)),
                "roc_auc": float(roc_auc_score(truth, calibrated)),
                "brier_score": float(brier_score_loss(truth, calibrated)),
                "folds": fold_rows,
                "raw": raw,
                "truth": truth,
                "present": np.asarray(oof_present, dtype=int),
                "calibrator": calibrator,
                "calibrated": calibrated,
            }

        selected_mode = max(
            mode_results, key=lambda mode: mode_results[mode]["pr_auc"]
        )
        selected = mode_results[selected_mode]
        self.calibrator = selected["calibrator"]
        self.change_threshold, sweep = self._threshold_sweep(
            selected["truth"],
            selected["calibrated"],
            getattr(config, "REGIME_MIN_CHANGE_PRECISION", 0.5),
        )
        min_precision = getattr(config, "REGIME_MIN_CHANGE_PRECISION", 0.5)
        self.regime_policies = {}
        for regime in MarketRegime:
            regime_mask = selected["present"] == int(regime)
            if not regime_mask.any() or len(np.unique(selected["truth"][regime_mask])) < 2:
                self.regime_policies[regime.name] = {
                    "threshold": self.change_threshold,
                    "gate_passed": False,
                    "gate_reasons": {"insufficient_validation_classes": False},
                    "validation_size": int(regime_mask.sum()),
                }
                continue
            regime_threshold, regime_sweep = self._threshold_sweep(
                selected["truth"][regime_mask],
                selected["calibrated"][regime_mask],
                min_precision,
            )
            validation_metrics = self._binary_metrics(
                selected["truth"][regime_mask],
                selected["calibrated"][regime_mask],
                regime_threshold,
            )
            policy_reasons = {
                "change_precision": (
                    validation_metrics["change_precision"] > min_precision
                ),
                "accuracy_vs_always_continue": (
                    validation_metrics["accuracy"]
                    > validation_metrics["always_continue_baseline"]
                ),
                "pr_auc_vs_prevalence": (
                    validation_metrics["pr_auc"] is not None
                    and validation_metrics["pr_auc"]
                    > validation_metrics["test_change_rate"]
                ),
            }
            self.regime_policies[regime.name] = {
                "threshold": regime_threshold,
                "gate_passed": all(policy_reasons.values()),
                "gate_reasons": policy_reasons,
                "validation_size": int(regime_mask.sum()),
                "validation_metrics": {
                    key: validation_metrics[key]
                    for key in (
                        "accuracy",
                        "always_continue_baseline",
                        "roc_auc",
                        "pr_auc",
                        "brier_score",
                        "change_precision",
                        "predicted_change_rate",
                        "test_change_rate",
                    )
                },
                "threshold_sweep": regime_sweep,
            }

        # Final model excludes a horizon-sized purge before untouched holdout.
        timestamps = df["timestamp"].astype(np.int64).to_numpy()
        holdout_start_time = int(timestamps[holdout_start])
        horizon_ms = self.horizon_hours * 60 * 60 * 1000
        final_train_idx = np.flatnonzero(
            timestamps[:holdout_start] + horizon_ms < holdout_start_time
        )
        holdout_idx = np.arange(holdout_start, len(df), dtype=int)
        self.scaler = StandardScaler()
        X_train = self.scaler.fit_transform(X_df.iloc[final_train_idx])
        X_holdout = self.scaler.transform(X_df.iloc[holdout_idx])
        self.model, class_weights = self._fit_booster(
            X_train, target.iloc[final_train_idx], selected_mode
        )
        holdout_raw = self.model.predict(xgb.DMatrix(X_holdout))
        holdout_prob = self._apply_calibrator(holdout_raw, self.calibrator)
        y_holdout = target.iloc[holdout_idx].to_numpy()
        present_holdout = df.iloc[holdout_idx]["regime_now"].astype(int).to_numpy()
        holdout_thresholds = np.array(
            [
                float(
                    self.regime_policies.get(
                        MarketRegime(int(regime)).name,
                        {"threshold": self.change_threshold},
                    )["threshold"]
                )
                for regime in present_holdout
            ]
        )
        metrics = self._binary_metrics(
            y_holdout, holdout_prob, holdout_thresholds
        )

        per_present: Dict[str, Any] = {}
        for regime in MarketRegime:
            mask = present_holdout == int(regime)
            if mask.any():
                policy = self.regime_policies[regime.name]
                holdout_regime_metrics = self._binary_metrics(
                    y_holdout[mask],
                    holdout_prob[mask],
                    float(policy["threshold"]),
                )
                holdout_gate_reasons = {
                    "change_precision": (
                        holdout_regime_metrics["change_precision"] > min_precision
                    ),
                    "accuracy_vs_always_continue": (
                        holdout_regime_metrics["accuracy"]
                        > holdout_regime_metrics["always_continue_baseline"]
                    ),
                    "pr_auc_vs_prevalence": (
                        holdout_regime_metrics["pr_auc"] is not None
                        and holdout_regime_metrics["pr_auc"]
                        > holdout_regime_metrics["test_change_rate"]
                    ),
                }
                # Deployment policy must pass both validation and untouched
                # holdout; a weak subgroup (e.g. TREND_DOWN) is suppressed.
                policy["holdout_gate_reasons"] = holdout_gate_reasons
                policy["holdout_gate_passed"] = all(
                    holdout_gate_reasons.values()
                )
                policy["alert_enabled"] = bool(
                    policy["gate_passed"] and policy["holdout_gate_passed"]
                )
                per_present[regime.name] = {
                    "threshold": policy["threshold"],
                    "alert_enabled": policy["alert_enabled"],
                    **holdout_regime_metrics,
                }

        self.gate_reasons = {
            "change_precision": metrics["change_precision"] > min_precision,
            "accuracy_vs_always_continue": (
                metrics["accuracy"] > metrics["always_continue_baseline"]
            ),
            "pr_auc_vs_prevalence": (
                metrics["pr_auc"] is not None
                and metrics["pr_auc"] > metrics["test_change_rate"]
            ),
        }
        self.gate_passed = all(self.gate_reasons.values())
        self.class_weight_mode = selected_mode
        self.target = "continue_change"
        self.model_version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        self.validation_summary = {
            "selected_class_weight": selected_mode,
            "candidate_modes": {
                mode: {
                    k: v
                    for k, v in result.items()
                    if k not in {
                        "raw",
                        "truth",
                        "present",
                        "calibrator",
                        "calibrated",
                    }
                }
                for mode, result in mode_results.items()
            },
            "selected_threshold": self.change_threshold,
            "threshold_sweep": sweep,
            "regime_policies": self.regime_policies,
        }
        self.save_model()

        result = {
            "success": True,
            "target": "continue_change",
            "label_version": self.label_version,
            "horizon_hours": self.horizon_hours,
            "change_threshold": self.change_threshold,
            "class_weight": selected_mode,
            "class_weights": class_weights,
            "calibration": (
                "platt" if getattr(self, "calibrator", None) is not None else "none"
            ),
            "gate_passed": self.gate_passed,
            "gate_reasons": self.gate_reasons,
            "model_version": self.model_version,
            "feature_schema_version": "transition_v1",
            "confirm_bars": getattr(config, "REGIME_CHANGE_CONFIRM_BARS", 2),
            "gate_requirements": {
                "change_precision_gt": min_precision,
                "accuracy_gt_always_continue": True,
                "pr_auc_gt_prevalence": True,
            },
            "train_size": len(final_train_idx),
            "holdout_size": len(holdout_idx),
            "holdout_start_ts": int(df.iloc[holdout_start]["timestamp"]),
            "purge_rows": self.horizon_hours,
            "feature_columns": available,
            "walk_forward": self.validation_summary,
            "per_present_regime": per_present,
            "regime_policies": self.regime_policies,
            "test_period": {
                "from_ts": int(df.iloc[holdout_start]["timestamp"]),
                "to_ts": int(df.iloc[-1]["timestamp"]),
            },
            "trained_at": datetime.now().isoformat(),
            **metrics,
            "beats_always_continue": (
                metrics["accuracy"] > metrics["always_continue_baseline"]
            ),
            "beats_majority": (
                metrics["accuracy"] > metrics["majority_baseline_accuracy"]
            ),
            "persistence_baseline_accuracy": metrics[
                "always_continue_baseline"
            ],
            "beats_persistence": (
                metrics["accuracy"] > metrics["always_continue_baseline"]
            ),
            "confusion_matrix_labels": ["CONTINUE", "CHANGE"],
        }
        logger.info(
            "confirmed-change(h=%s) holdout_acc=%.4f continue=%.4f "
            "pr_auc=%.4f prevalence=%.4f precision=%.4f gate=%s",
            self.horizon_hours,
            metrics["accuracy"],
            metrics["always_continue_baseline"],
            metrics["pr_auc"],
            metrics["test_change_rate"],
            metrics["change_precision"],
            self.gate_passed,
        )
        return result

    def _train_model_legacy_reference(
        self,
        inst_id: str = "ETH-USDT-SWAP",
        bar: str = "1H",
        limit: int = 10000,
        test_ratio: float = 0.2,
        class_weight: Optional[str] = None,
        horizon_hours: Optional[int] = None,
    ) -> Dict[str, Any]:
        if horizon_hours is not None:
            self.horizon_hours = int(horizon_hours)
            self._labeler = RegimeLabeler(horizon_hours=self.horizon_hours)

        weight_mode = (class_weight or self.class_weight_mode or "none").strip().lower()
        if weight_mode not in ("balanced", "none"):
            raise ValueError("class_weight must be 'balanced' or 'none'")

        features = feature_handler.get_features_for_regime(
            inst_id=inst_id, bar=bar, limit=limit
        )
        if not features or len(features) < 200:
            raise ValueError(
                f"forward-labeled samples insufficient: {len(features) if features else 0}"
            )

        df = pd.DataFrame(features)
        df = df.dropna(subset=["regime_48h", "regime_now"])
        df = df.sort_values("timestamp").reset_index(drop=True)

        present = self._present_series(df).astype(int)
        future = df["regime_48h"].astype(int)
        # 1 = structure changes within horizon; 0 = continues
        targets = (future != present).astype(int)

        available = [c for c in REGIME_FEATURE_COLUMNS if c in df.columns]
        if not available:
            raise ValueError("no regime feature columns available")

        self.feature_columns = available
        features_df = df[available].ffill().fillna(0)

        split_idx = int(len(features_df) * (1 - test_ratio))
        if split_idx < 50 or (len(features_df) - split_idx) < 20:
            raise ValueError("train/test split too small")

        X_train = features_df.iloc[:split_idx]
        X_test = features_df.iloc[split_idx:]
        y_train = targets.iloc[:split_idx]
        y_test = targets.iloc[split_idx:]

        train_weights = None
        class_weight_used: Dict[str, float] = {}
        if weight_mode == "balanced":
            train_weights, class_weight_used = self._balanced_sample_weights(y_train)
            logger.info("Using balanced class weights: %s", class_weight_used)

        logger.info(
            "Continue/change(h=%s) train=%s test=%s features=%s weight=%s",
            self.horizon_hours,
            len(X_train),
            len(X_test),
            len(available),
            weight_mode,
        )
        logger.info("Train transition dist:\n%s", y_train.value_counts().sort_index())
        logger.info("Test  transition dist:\n%s", y_test.value_counts().sort_index())

        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        params = {
            "objective": "binary:logistic",
            "max_depth": 6,
            "learning_rate": 0.05,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "min_child_weight": 5,
            "gamma": 0.1,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
            "random_state": 42,
            "eval_metric": "logloss",
        }

        dtrain = xgb.DMatrix(X_train_scaled, label=y_train, weight=train_weights)
        dtest = xgb.DMatrix(X_test_scaled, label=y_test)

        self.model = xgb.train(
            params,
            dtrain,
            num_boost_round=150,
            evals=[(dtrain, "train"), (dtest, "test")],
            early_stopping_rounds=15,
            verbose_eval=False,
        )

        y_prob = self.model.predict(dtest)
        y_pred = (y_prob >= self.change_threshold).astype(int)
        accuracy = float(accuracy_score(y_test, y_pred))

        # Strong baseline: always predict CONTINUE (structure persists)
        always_continue = float(accuracy_score(y_test, np.zeros(len(y_test), dtype=int)))
        always_change = float(accuracy_score(y_test, np.ones(len(y_test), dtype=int)))
        majority = max(always_continue, always_change)

        try:
            roc_auc = float(roc_auc_score(y_test, y_prob))
        except ValueError:
            roc_auc = None

        report = classification_report(
            y_test,
            y_pred,
            labels=[CONTINUE, CHANGE],
            target_names=["CONTINUE", "CHANGE"],
            output_dict=True,
            zero_division=0,
        )
        conf = confusion_matrix(y_test, y_pred, labels=[CONTINUE, CHANGE]).tolist()

        self.class_weight_mode = weight_mode
        self.target = "continue_change"
        self.save_model()

        change_rate = float(y_test.mean())
        results = {
            "success": True,
            "target": "continue_change",
            "horizon_hours": self.horizon_hours,
            "change_threshold": self.change_threshold,
            "class_weight": weight_mode,
            "class_weights": class_weight_used,
            "accuracy": accuracy,
            "always_continue_baseline": always_continue,
            "always_change_baseline": always_change,
            "majority_baseline_accuracy": majority,
            "beats_always_continue": accuracy > always_continue,
            "beats_majority": accuracy > majority,
            "roc_auc": roc_auc,
            "test_change_rate": round(change_rate, 4),
            "train_size": len(X_train),
            "test_size": len(X_test),
            "feature_columns": available,
            "classification_report": report,
            "confusion_matrix": conf,
            "confusion_matrix_labels": ["CONTINUE", "CHANGE"],
            "test_period": {
                "from_ts": int(df.iloc[split_idx]["timestamp"]),
                "to_ts": int(df.iloc[-1]["timestamp"]),
            },
            "trained_at": datetime.now().isoformat(),
            # Compat aliases for old pipeline summary readers
            "persistence_baseline_accuracy": always_continue,
            "beats_persistence": accuracy > always_continue,
        }
        logger.info(
            "continue/change(h=%s) acc=%.4f always_continue=%.4f roc_auc=%s "
            "beats_continue=%s weight=%s",
            self.horizon_hours,
            accuracy,
            always_continue,
            f"{roc_auc:.4f}" if roc_auc is not None else "n/a",
            results["beats_always_continue"],
            weight_mode,
        )
        return results

    def predict_proba_change(
        self, features_input: Union[pd.DataFrame, List[Dict[str, Any]], List[Feature]]
    ) -> np.ndarray:
        """P(change) for each row."""
        if self.model is None or self.feature_columns is None:
            raise ValueError("Model not loaded")

        if isinstance(features_input, list):
            rows = []
            for item in features_input:
                rows.append(item.to_dict() if isinstance(item, Feature) else item)
            features_df = pd.DataFrame(rows)
        else:
            features_df = features_input.copy()

        if (
            "dynamic_features_ready" not in features_df.columns
            or not features_df["dynamic_features_ready"].fillna(False).all()
            or "feature_schema_version" not in features_df.columns
            or not (
                features_df["feature_schema_version"] == "transition_v1"
            ).all()
        ):
            raise ValueError(
                "transition features are not ready/current; ensure at least "
                "12 historical feature rows and re-run merge-features"
            )

        # FeatureMerge persists the exact lag/dynamic fields used in training.
        # Missing fields are a schema error rather than silently forcing a
        # train-serving-skewed constant.
        missing = [c for c in self.feature_columns if c not in features_df.columns]
        if missing:
            raise ValueError(
                "prediction feature schema is stale; re-run merge-features. "
                f"Missing: {missing}"
            )
        features_df = features_df[self.feature_columns].fillna(0)
        scaled = self.scaler.transform(features_df)
        raw = self.model.predict(xgb.DMatrix(scaled))
        return self._apply_calibrator(raw, self.calibrator)

    def _thresholds_for_rows(self, features_df: pd.DataFrame) -> np.ndarray:
        """Per-row thresholds from present-regime policies (fallback: global)."""
        default = float(self.change_threshold)
        if "regime_now" not in features_df.columns or not self.regime_policies:
            return np.full(len(features_df), default, dtype=float)
        thresholds = []
        for value in features_df["regime_now"].tolist():
            try:
                name = MarketRegime(int(value)).name
            except (TypeError, ValueError):
                thresholds.append(default)
                continue
            policy = self.regime_policies.get(name) or {}
            thresholds.append(float(policy.get("threshold", default)))
        return np.asarray(thresholds, dtype=float)

    def predict(
        self, features_input: Union[pd.DataFrame, List[Dict[str, Any]], List[Feature]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Backward-compatible shape: predictions are 0/1 (continue/change),
        probabilities are [[p_continue, p_change], ...].

        Decision uses present-regime-specific thresholds when available.
        """
        if isinstance(features_input, list):
            rows = []
            for item in features_input:
                rows.append(item.to_dict() if isinstance(item, Feature) else item)
            features_df = pd.DataFrame(rows)
        else:
            features_df = features_input.copy()

        p_change = self.predict_proba_change(features_df)
        thresholds = self._thresholds_for_rows(features_df)
        preds = (p_change >= thresholds).astype(int)
        probs = np.column_stack([1.0 - p_change, p_change])
        return preds, probs

    def predict_single(
        self, feature_input: Union[Dict[str, Any], Feature]
    ) -> Tuple[int, np.ndarray, str, float]:
        """
        Returns:
            change_flag (0/1), probs [p_continue, p_change], unused strategy, confidence
        """
        feature_dict = (
            feature_input.to_dict()
            if isinstance(feature_input, Feature)
            else feature_input
        )
        preds, probs = self.predict([feature_dict])
        change_flag = int(preds[0])
        confidence = float(probs[0][change_flag])
        return change_flag, probs[0], "n/a", confidence

    def build_prediction_payload(
        self, feature_input: Union[Dict[str, Any], Feature]
    ) -> Dict[str, Any]:
        """Rules=present; model=P(change) over horizon."""
        feature_dict = (
            feature_input.to_dict()
            if isinstance(feature_input, Feature)
            else feature_input
        )

        present_regime = self._labeler.classify(feature_dict)
        present_enum = MarketRegime(present_regime)

        _change_flag, probs, _s, _c = self.predict_single(feature_dict)
        p_continue = float(probs[0])
        p_change = float(probs[1])
        regime_policy = self.regime_policies.get(
            present_enum.name,
            {
                "threshold": self.change_threshold,
                "alert_enabled": False,
                "gate_reasons": {"missing_regime_policy": False},
            },
        )
        active_threshold = float(
            regime_policy.get("threshold", self.change_threshold)
        )
        changes = bool(p_change >= active_threshold)
        continues = not changes
        regime_gate_passed = bool(regime_policy.get("alert_enabled", False))

        transition = {
            "source": "model",
            "horizon_hours": self.horizon_hours,
            "continues": continues,
            "changes": changes,
            "p_continue": round(p_continue, 4),
            "p_change": round(p_change, 4),
            "threshold": active_threshold,
            "present_regime_policy": present_enum.name,
            "prediction": "CHANGE" if changes else "CONTINUE",
            "model_gate_passed": bool(
                getattr(self, "gate_passed", False) and regime_gate_passed
            ),
            "gate_reasons": regime_policy.get("holdout_gate_reasons")
            or regime_policy.get("gate_reasons", {}),
            "alert_eligible": bool(
                getattr(self, "gate_passed", False)
                and regime_gate_passed
                and changes
            ),
        }

        payload = {
            "type": "regime",
            "target": "continue_change",
            "timestamp": feature_dict.get("timestamp"),
            "inst_id": feature_dict.get("inst_id", "ETH-USDT-SWAP"),
            "bar": feature_dict.get("bar", "1H"),
            "price": feature_dict.get("price"),
            "features_count": len(self.feature_columns or []),
            "horizon_hours": self.horizon_hours,
            "class_weight": self.class_weight_mode,
            "model_gate_passed": bool(getattr(self, "gate_passed", False)),
            "model_version": getattr(self, "model_version", "unknown"),
            "calibration": (
                "platt" if getattr(self, "calibrator", None) is not None else "none"
            ),
            "present": {
                "regime": present_regime,
                "regime_label": REGIME_LABELS.get(present_enum, str(present_regime)),
                "source": "rules",
                "recommended_strategy": REGIME_STRATEGY.get(present_enum, "none"),
                "regime_description": REGIME_DESCRIPTION.get(present_enum, ""),
            },
            "transition": transition,
            "derived": {
                "continues": continues,
                "changes": changes,
                "p_continue": round(p_continue, 4),
                "p_change": round(p_change, 4),
            },
            # Flat fields: present structure (strategy from rules); confidence = P(predicted class)
            "regime": present_regime,
            "regime_label": REGIME_LABELS.get(present_enum, str(present_regime)),
            "regime_description": REGIME_DESCRIPTION.get(present_enum, ""),
            "recommended_strategy": REGIME_STRATEGY.get(present_enum, "none"),
            "confidence": round(max(p_continue, p_change), 4),
            "probabilities": {
                "continue": round(p_continue, 4),
                "change": round(p_change, 4),
            },
        }
        return payload

    def save_model(self):
        if self.model is None:
            return
        os.makedirs(os.path.dirname(self.model_save_path) or ".", exist_ok=True)
        model_path = self.model_save_path
        scaler_path = model_path.replace(".json", "_scaler.pkl")
        calibrator_path = model_path.replace(".json", "_calibrator.pkl")
        features_path = model_path.replace(".json", "_features.json")
        meta_path = model_path.replace(".json", "_meta.json")
        tmp_model = model_path.replace(".json", "_tmp.json")
        tmp_scaler = scaler_path + ".tmp"
        tmp_calibrator = calibrator_path + ".tmp"
        tmp_features = features_path + ".tmp"
        tmp_meta = meta_path + ".tmp"

        # Write a complete generation to temporary paths; metadata is replaced
        # last and acts as the generation commit marker.
        self.model.save_model(tmp_model)
        joblib.dump(self.scaler, tmp_scaler)
        joblib.dump(self.calibrator, tmp_calibrator)
        with open(tmp_features, "w") as f:
            json.dump(self.feature_columns, f)
        meta = {
            "target": "continue_change",
            "model_version": self.model_version,
            "horizon_hours": self.horizon_hours,
            "confirm_bars": getattr(config, "REGIME_CHANGE_CONFIRM_BARS", 2),
            "class_weight": self.class_weight_mode,
            "change_threshold": self.change_threshold,
            "label_version": self.label_version,
            "feature_schema_version": "transition_v1",
            "gate_passed": self.gate_passed,
            "gate_reasons": self.gate_reasons,
            "regime_policies": self.regime_policies,
            "validation_summary": self.validation_summary,
            "trained_at": datetime.now().isoformat(),
        }
        with open(tmp_meta, "w") as f:
            json.dump(meta, f)
        os.replace(tmp_model, model_path)
        os.replace(tmp_scaler, scaler_path)
        os.replace(tmp_calibrator, calibrator_path)
        os.replace(tmp_features, features_path)
        os.replace(tmp_meta, meta_path)
        logger.info(
            "Continue/change model saved to %s (horizon=%sh weight=%s)",
            self.model_save_path,
            self.horizon_hours,
            self.class_weight_mode,
        )

    def load_model(self) -> bool:
        try:
            if not os.path.exists(self.model_save_path):
                logger.warning("Regime model not found: %s", self.model_save_path)
                return False
            self.model = xgb.Booster()
            self.model.load_model(self.model_save_path)
            self.scaler = joblib.load(
                self.model_save_path.replace(".json", "_scaler.pkl")
            )
            calibrator_path = self.model_save_path.replace(
                ".json", "_calibrator.pkl"
            )
            self.calibrator = (
                joblib.load(calibrator_path)
                if os.path.exists(calibrator_path)
                else None
            )
            with open(self.model_save_path.replace(".json", "_features.json")) as f:
                self.feature_columns = json.load(f)
            meta_path = self.model_save_path.replace(".json", "_meta.json")
            if os.path.exists(meta_path):
                with open(meta_path) as f:
                    meta = json.load(f)
                self.target = meta.get("target", "continue_change")
                self.horizon_hours = int(
                    meta.get("horizon_hours")
                    or getattr(config, "REGIME_HORIZON_HOURS", 48)
                )
                self.class_weight_mode = meta.get(
                    "class_weight",
                    getattr(config, "REGIME_CLASS_WEIGHT", "balanced"),
                )
                self.change_threshold = float(
                    meta.get(
                        "change_threshold",
                        getattr(config, "REGIME_CHANGE_THRESHOLD", 0.5),
                    )
                )
                self.label_version = meta.get(
                    "label_version", "endpoint_change_legacy"
                )
                self.gate_passed = bool(meta.get("gate_passed", False))
                self.gate_reasons = meta.get("gate_reasons") or {}
                self.regime_policies = meta.get("regime_policies") or {}
                self.model_version = meta.get("model_version", "unknown")
                self.validation_summary = meta.get("validation_summary") or {}
                self._labeler = RegimeLabeler(horizon_hours=self.horizon_hours)
                if self.target not in ("continue_change", "regime_48h"):
                    logger.warning("Unknown model target in meta: %s", self.target)
                if self.target == "regime_48h":
                    logger.error(
                        "Loaded legacy 3-class regime model; re-run /regime/2-train "
                        "for continue/change."
                    )
                    return False
                if self.label_version != "confirmed_change_v1":
                    logger.error(
                        "Loaded legacy endpoint-change model; re-run merge, full "
                        "label, and /regime/2-train for confirmed-change."
                    )
                    return False
                if meta.get("feature_schema_version") != "transition_v1":
                    logger.error("Model feature schema version is stale")
                    return False
                if int(meta.get("confirm_bars") or -1) != int(
                    getattr(config, "REGIME_CHANGE_CONFIRM_BARS", 2)
                ):
                    logger.error(
                        "Model confirmation bars do not match runtime config"
                    )
                    return False
                missing_dynamic = [
                    column
                    for column in TRANSITION_DYNAMIC_COLUMNS
                    if column not in (self.feature_columns or [])
                ]
                if missing_dynamic:
                    logger.error(
                        "Loaded model lacks transition feature schema: %s",
                        missing_dynamic,
                    )
                    return False
            return True
        except Exception as e:
            logger.error("Failed to load regime model: %s", e)
            return False


regime_trainer = RegimeTrainer()
