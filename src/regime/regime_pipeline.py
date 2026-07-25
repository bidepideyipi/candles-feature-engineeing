"""
Regime 训练流水线：拉取 → 连续性校验 → 合并特征 → regime 标注 → 训练 → 聚合报告。
"""
from __future__ import annotations

import logging
import math
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from collect.candlestick_continuity import (
    DEFAULT_BARS,
    candlestick_continuity_checker,
)
from collect.candlestick_handler import candlestick_handler
from collect.feature_handler import feature_handler
from collect.okex_fetcher import okex_fetcher
from feature.feature_merge import FeatureMerge
from models.regime_trainer import regime_trainer
from regime.regime_labeler import RegimeLabeler
from regime.regime_types import REGIME_LABELS, MarketRegime

logger = logging.getLogger(__name__)

# 相对 1H 覆盖同一时间跨度的条数倍率（与 /fetch/1-pull-history 文档一致）
BAR_RECORDS_FROM_1H = {
    "15m": 4,
    "1H": 1,
    "4H": 0.25,
    "1D": 1 / 24,
}

# OKEx 单次拉取接口上限（与 api_fetch_okex 一致）
MAX_PULL_RECORDS = 10000
PULL_ORDER = ("1D", "4H", "1H", "15m")


class RegimePipeline:
    """一步完成 regime 从数据采集到训练报告。"""

    def run(
        self,
        inst_id: str = "ETH-USDT-SWAP",
        max_records_1h: int = 2400,
        skip_pull: bool = False,
        strict_continuity: bool = True,
        merge_limit: int = 5000,
        label_limit: int = 50000,
        only_fix_none_label: bool = True,
        train_limit: int = 10000,
        test_ratio: float = 0.2,
        bars: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        bars = list(bars or DEFAULT_BARS)
        started = datetime.now()
        t0 = time.monotonic()

        report: Dict[str, Any] = {
            "success": False,
            "inst_id": inst_id,
            "started_at": started.isoformat(),
            "finished_at": None,
            "elapsed_seconds": None,
            "failed_step": None,
            "message": "",
            "steps": {},
            "summary": {},
        }

        # ---- 1. pull ----
        if skip_pull:
            pull_result = {
                "skipped": True,
                "success": True,
                "message": "跳过拉取，使用已有 K 线",
                "counts": self._candle_counts(inst_id, bars),
            }
        else:
            pull_result = self._step_pull(inst_id=inst_id, max_records_1h=max_records_1h, bars=bars)
        report["steps"]["pull"] = pull_result
        if not pull_result.get("success"):
            return self._fail(report, "pull", pull_result.get("message", "拉取失败"), t0)

        # ---- 2. continuity ----
        continuity = candlestick_continuity_checker.check_all(inst_id=inst_id, bars=bars)
        report["steps"]["continuity"] = continuity
        if strict_continuity and not continuity.get("ok"):
            return self._fail(
                report,
                "continuity",
                continuity.get("message", "K 线不连续"),
                t0,
            )

        # ---- 3. merge features ----
        merge_result = self._step_merge(merge_limit=merge_limit)
        report["steps"]["merge"] = merge_result
        if not merge_result.get("success"):
            return self._fail(
                report,
                "merge",
                merge_result.get("last_error") or "特征合并失败",
                t0,
            )

        # ---- 4. regime label ----
        label_result = RegimeLabeler().loop(
            inst_id=inst_id,
            limit=label_limit,
            only_fix_none=only_fix_none_label,
            bar="1H",
        )
        report["steps"]["label"] = label_result
        if not label_result.get("success"):
            return self._fail(
                report,
                "label",
                label_result.get("message", "regime 标注失败"),
                t0,
            )

        # ---- 5. train ----
        try:
            train_result = regime_trainer.train_model(
                inst_id=inst_id,
                limit=train_limit,
                test_ratio=test_ratio,
            )
            train_result = {"success": True, **train_result}
        except ValueError as e:
            train_result = {"success": False, "message": str(e)}
        except Exception as e:
            logger.exception("regime 训练异常")
            train_result = {"success": False, "message": str(e)}

        report["steps"]["train"] = train_result
        if not train_result.get("success"):
            return self._fail(
                report,
                "train",
                train_result.get("message", "训练失败"),
                t0,
            )

        report["success"] = True
        report["message"] = "流水线完成"
        report["summary"] = self._build_summary(
            inst_id=inst_id,
            bars=bars,
            continuity=continuity,
            merge_result=merge_result,
            label_result=label_result,
            train_result=train_result,
        )
        return self._finish(report, t0)

    def _step_pull(
        self, inst_id: str, max_records_1h: int, bars: List[str]
    ) -> Dict[str, Any]:
        if max_records_1h < 1:
            return {"success": False, "message": "max_records_1h 必须 >= 1", "by_bar": {}}

        targets = self._plan_pull_counts(max_records_1h, bars)
        by_bar: Dict[str, Any] = {}
        all_ok = True

        for bar in PULL_ORDER:
            if bar not in targets:
                continue
            n = targets[bar]
            try:
                ok = okex_fetcher.fetch_historical_data(
                    inst_id=inst_id, bar=bar, max_records=n
                )
            except Exception as e:
                logger.exception("拉取 %s 失败", bar)
                ok = False
                by_bar[bar] = {
                    "requested": n,
                    "success": False,
                    "error": str(e),
                    "count_after": candlestick_handler.count(inst_id, bar),
                }
                all_ok = False
                continue

            count_after = candlestick_handler.count(inst_id, bar)
            by_bar[bar] = {
                "requested": n,
                "success": bool(ok),
                "count_after": count_after,
            }
            if not ok:
                all_ok = False

        return {
            "skipped": False,
            "success": all_ok,
            "max_records_1h": max_records_1h,
            "targets": targets,
            "by_bar": by_bar,
            "counts": self._candle_counts(inst_id, bars),
            "message": "拉取完成" if all_ok else "部分时间维度拉取失败",
        }

    def _plan_pull_counts(
        self, max_records_1h: int, bars: List[str]
    ) -> Dict[str, int]:
        targets: Dict[str, int] = {}
        for bar in bars:
            scale = BAR_RECORDS_FROM_1H.get(bar)
            if scale is None:
                continue
            n = max(1, int(math.ceil(max_records_1h * scale)))
            targets[bar] = min(n, MAX_PULL_RECORDS)
        return targets

    def _step_merge(self, merge_limit: int) -> Dict[str, Any]:
        feature_merge = FeatureMerge()
        stats = feature_merge.loop(limit=merge_limit)
        stats["features_in_db"] = feature_handler.count_features(
            inst_id=feature_merge.inst_id, bar="1H"
        )
        return stats

    def _candle_counts(self, inst_id: str, bars: List[str]) -> Dict[str, int]:
        return {bar: candlestick_handler.count(inst_id, bar) for bar in bars}

    def _build_summary(
        self,
        inst_id: str,
        bars: List[str],
        continuity: Dict[str, Any],
        merge_result: Dict[str, Any],
        label_result: Dict[str, Any],
        train_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        report = train_result.get("classification_report") or {}
        per_class = {}
        for regime in MarketRegime:
            name = REGIME_LABELS[regime]
            metrics = report.get(name) or report.get(str(int(regime) - 1))
            if isinstance(metrics, dict):
                per_class[name] = {
                    "precision": round(float(metrics.get("precision", 0)), 4),
                    "recall": round(float(metrics.get("recall", 0)), 4),
                    "f1": round(float(metrics.get("f1-score", 0)), 4),
                    "support": int(metrics.get("support", 0)),
                }

        return {
            "continuity_ok": bool(continuity.get("ok")),
            "failed_bars": continuity.get("failed_bars") or [],
            "candlestick_counts": self._candle_counts(inst_id, bars),
            "features_merged": merge_result.get("processed", 0),
            "features_in_db": merge_result.get("features_in_db")
            or feature_handler.count_features(inst_id=inst_id, bar="1H"),
            "regime_labeled": label_result.get("labeled_after"),
            "regime_distribution": label_result.get("regime_distribution"),
            "accuracy": train_result.get("accuracy"),
            "train_size": train_result.get("train_size"),
            "test_size": train_result.get("test_size"),
            "test_period": train_result.get("test_period"),
            "feature_columns_count": len(train_result.get("feature_columns") or []),
            "per_class": per_class,
            "confusion_matrix": train_result.get("confusion_matrix"),
            "trained_at": train_result.get("trained_at"),
            "macro_f1": self._safe_nested(report, "macro avg", "f1-score"),
            "weighted_f1": self._safe_nested(report, "weighted avg", "f1-score"),
        }

    @staticmethod
    def _safe_nested(d: Dict[str, Any], *keys: str) -> Optional[float]:
        cur: Any = d
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return None
            cur = cur[k]
        try:
            return round(float(cur), 4)
        except (TypeError, ValueError):
            return None

    def _fail(
        self, report: Dict[str, Any], step: str, message: str, t0: float
    ) -> Dict[str, Any]:
        report["success"] = False
        report["failed_step"] = step
        report["message"] = message
        report["summary"] = {
            "failed_step": step,
            "message": message,
            "candlestick_counts": report.get("steps", {}).get("pull", {}).get("counts"),
            "continuity_ok": (report.get("steps", {}).get("continuity") or {}).get("ok"),
        }
        return self._finish(report, t0)

    def _finish(self, report: Dict[str, Any], t0: float) -> Dict[str, Any]:
        report["finished_at"] = datetime.now().isoformat()
        report["elapsed_seconds"] = round(time.monotonic() - t0, 2)
        return report


regime_pipeline = RegimePipeline()
