"""
Rule-based present regime + forward horizon label for model training.

- regime_now: structure at T (rules)
- regime_48h: structure at T+REGIME_HORIZON_HOURS via same rules (model target;
  Mongo field name kept for compatibility)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from config.settings import config
from regime.regime_types import (
    MS_PER_HOUR,
    REGIME_HORIZON_HOURS_DEFAULT,
    MarketRegime,
)

log = logging.getLogger(__name__)


class RegimeLabeler:
    ADX_TREND_THRESHOLD = 20.0
    ADX_RANGE_THRESHOLD = 18.0
    # Cross-TF atr_ratio_4h_1h = ATR(4H)/ATR(1H). √4≈2 is geometric scale;
    # below this, 1H noise dominates → force RANGE.
    ATR_RATIO_RANGE_MAX = 2.0
    TREND_CONT_THRESHOLD = 0.0

    def __init__(self, horizon_hours: Optional[int] = None):
        hours = horizon_hours
        if hours is None:
            hours = getattr(config, "REGIME_HORIZON_HOURS", REGIME_HORIZON_HOURS_DEFAULT)
        self.horizon_hours = int(hours)
        self.horizon_ms = self.horizon_hours * MS_PER_HOUR
        self.confirm_bars = max(
            1, int(getattr(config, "REGIME_CHANGE_CONFIRM_BARS", 2))
        )

    def classify(self, feature: Dict[str, Any]) -> int:
        adx = float(feature.get("adx_4h") or 0)
        plus_di = float(feature.get("plus_di_4h") or 0)
        minus_di = float(feature.get("minus_di_4h") or 0)
        trend_cont = float(feature.get("trend_continuation_4h") or 0)
        ema_cross = int(feature.get("ema_cross_4h_12_26") or 0)
        atr_ratio = float(feature.get("atr_ratio_4h_1h") or 1.0)
        macd_hist = float(feature.get("macd_histogram_4h") or 0)
        ema_12 = float(feature.get("ema_12_4h") or 0)
        ema_26 = float(feature.get("ema_26_4h") or 0)

        if self._is_range(adx, atr_ratio, trend_cont):
            return int(MarketRegime.RANGE)

        bullish = (
            plus_di > minus_di
            and (ema_cross >= 0 or trend_cont > self.TREND_CONT_THRESHOLD)
            and (ema_12 >= ema_26 or macd_hist >= 0)
        )
        bearish = (
            minus_di > plus_di
            and (ema_cross <= 0 or trend_cont < -self.TREND_CONT_THRESHOLD)
            and (ema_12 <= ema_26 or macd_hist <= 0)
        )

        if adx >= self.ADX_TREND_THRESHOLD and bullish:
            return int(MarketRegime.TREND_UP)
        if adx >= self.ADX_TREND_THRESHOLD and bearish:
            return int(MarketRegime.TREND_DOWN)

        return int(MarketRegime.RANGE)

    def _is_range(self, adx: float, atr_ratio: float, trend_cont: float) -> bool:
        if adx < self.ADX_RANGE_THRESHOLD:
            return True
        if atr_ratio < self.ATR_RATIO_RANGE_MAX:
            return True
        if abs(trend_cont) < 0.15 and adx < self.ADX_TREND_THRESHOLD:
            return True
        return False

    @staticmethod
    def _present_missing(feature: Dict[str, Any]) -> bool:
        return feature.get("regime_now") is None

    def _future_missing(self, feature: Dict[str, Any]) -> bool:
        return (
            feature.get("regime_48h") is None
            or feature.get("transition_confirmed_change") is None
            or int(feature.get("regime_horizon_hours") or -1) != self.horizon_hours
            or int(feature.get("transition_confirm_bars") or -1) != self.confirm_bars
        )

    def _confirmed_change(
        self,
        present_regime: int,
        future_rows: List[Dict[str, Any]],
    ) -> tuple[int, Optional[int]]:
        """Any different regime persisting for confirm_bars within the horizon."""
        streak = 0
        candidate: Optional[int] = None
        for hour, row in enumerate(future_rows, start=1):
            regime = self.classify(row)
            if regime == present_regime:
                candidate = None
                streak = 0
                continue
            if regime == candidate:
                streak += 1
            else:
                candidate = regime
                streak = 1
            if streak >= self.confirm_bars:
                return 1, hour - self.confirm_bars + 1
        return 0, None

    def loop(
        self,
        inst_id: str,
        limit: int = 50000,
        only_fix_none: bool = True,
        bar: str = "1H",
    ) -> Dict[str, Any]:
        """
        Dual-track labeling on 1H features.
        Loads enough rows to resolve T+horizon for the batch being written.
        """
        from collect.feature_handler import feature_handler

        total_in_db = feature_handler.count_features(inst_id=inst_id, bar=bar)
        labeled_before = feature_handler.count_regime_labeled(inst_id=inst_id, bar=bar)
        labeled_48h_before = feature_handler.count_regime_48h_labeled(
            inst_id=inst_id, bar=bar
        )

        # Fetch a window large enough that older rows can see T+48h inside the set.
        fetch_limit = min(max(limit + self.horizon_hours + 8, limit), 200000)
        lookup_rows = feature_handler.get_all_features(
            inst_id=inst_id, bar=bar, limit=fetch_limit
        )
        if not lookup_rows:
            log.warning("无 feature 可标注 regime, inst_id=%s bar=%s", inst_id, bar)
            return {
                "success": False,
                "inst_id": inst_id,
                "bar": bar,
                "only_fix_none": only_fix_none,
                "horizon_hours": self.horizon_hours,
                "total_in_db": total_in_db,
                "labeled_before": labeled_before,
                "labeled_48h_before": labeled_48h_before,
                "processed": 0,
                "matched": 0,
                "modified": 0,
                "unchanged": 0,
                "regime_48h_set": 0,
                "regime_48h_cleared": 0,
                "message": "未找到可处理的 feature，请先执行 /regime/pipeline",
            }

        by_ts: Dict[int, Dict[str, Any]] = {}
        for row in lookup_rows:
            ts = row.get("timestamp")
            if ts is not None:
                by_ts[int(ts)] = row

        # Process newest `limit` rows (stable product behavior).
        candidates = sorted(
            lookup_rows, key=lambda r: int(r.get("timestamp") or 0), reverse=True
        )[:limit]

        matched = 0
        modified = 0
        unchanged = 0
        regime_now_counts: Dict[int, int] = {}
        regime_48h_counts: Dict[int, int] = {}
        regime_48h_set = 0
        regime_48h_cleared = 0
        endpoint_change_count = 0
        confirmed_change_count = 0
        complete_by_present: Dict[int, int] = {}
        confirmed_by_present: Dict[int, int] = {}
        confirmed_lag_hours: List[int] = []
        skipped = 0

        for feature in candidates:
            ts = feature.get("timestamp")
            if ts is None:
                skipped += 1
                continue
            ts = int(ts)

            need_present = (not only_fix_none) or self._present_missing(feature)
            need_future = (not only_fix_none) or self._future_missing(feature)
            if only_fix_none and not need_present and not need_future:
                skipped += 1
                continue

            regime_now = (
                self.classify(feature)
                if need_present
                else int(feature["regime_now"])
            )
            regime_now_counts[regime_now] = regime_now_counts.get(regime_now, 0) + 1

            future_rows = [
                by_ts.get(ts + hour * MS_PER_HOUR)
                for hour in range(1, self.horizon_hours + 1)
            ]
            if all(row is not None for row in future_rows):
                complete_future_rows = [row for row in future_rows if row is not None]
                future_row = complete_future_rows[-1]
                regime_48h: Optional[int] = self.classify(future_row)
                regime_48h_counts[regime_48h] = regime_48h_counts.get(regime_48h, 0) + 1
                endpoint_change = int(regime_48h != regime_now)
                confirmed_change, first_change_hour = self._confirmed_change(
                    regime_now, complete_future_rows
                )
                endpoint_change_count += endpoint_change
                confirmed_change_count += confirmed_change
                complete_by_present[regime_now] = (
                    complete_by_present.get(regime_now, 0) + 1
                )
                confirmed_by_present[regime_now] = (
                    confirmed_by_present.get(regime_now, 0) + confirmed_change
                )
                if first_change_hour is not None:
                    confirmed_lag_hours.append(first_change_hour)
                clear_48h = False
                regime_48h_set += 1
            else:
                regime_48h = None
                endpoint_change = None
                confirmed_change = None
                clear_48h = True
                regime_48h_cleared += 1

            result = feature_handler.update_regime_labels(
                inst_id=inst_id,
                timestamp=ts,
                regime_now=regime_now,
                regime_48h=regime_48h,
                horizon_hours=self.horizon_hours,
                endpoint_change=endpoint_change,
                confirmed_change=confirmed_change,
                confirm_bars=self.confirm_bars,
                bar=bar,
                clear_48h=clear_48h,
            )
            if result["matched"] > 0:
                matched += 1
                if result["modified"] > 0:
                    modified += 1
                else:
                    unchanged += 1

        labeled_after = feature_handler.count_regime_labeled(inst_id=inst_id, bar=bar)
        labeled_48h_after = feature_handler.count_regime_48h_labeled(
            inst_id=inst_id, bar=bar
        )

        log.info(
            "regime dual-label inst_id=%s processed=%s matched=%s modified=%s "
            "48h_set=%s 48h_cleared=%s",
            inst_id,
            len(candidates),
            matched,
            modified,
            regime_48h_set,
            regime_48h_cleared,
        )

        return {
            "success": matched > 0,
            "inst_id": inst_id,
            "bar": bar,
            "only_fix_none": only_fix_none,
            "horizon_hours": self.horizon_hours,
            "confirm_bars": self.confirm_bars,
            "total_in_db": total_in_db,
            "labeled_before": labeled_before,
            "labeled_after": labeled_after,
            "labeled_48h_before": labeled_48h_before,
            "labeled_48h_after": labeled_48h_after,
            "processed": len(candidates) - skipped,
            "skipped": skipped,
            "matched": matched,
            "modified": modified,
            "unchanged": unchanged,
            "regime_48h_set": regime_48h_set,
            "regime_48h_cleared": regime_48h_cleared,
            "endpoint_change_count": endpoint_change_count,
            "confirmed_change_count": confirmed_change_count,
            "endpoint_change_rate": round(
                endpoint_change_count / regime_48h_set, 4
            ) if regime_48h_set else None,
            "confirmed_change_rate": round(
                confirmed_change_count / regime_48h_set, 4
            ) if regime_48h_set else None,
            "confirmed_change_rate_by_present": {
                MarketRegime(k).name: round(
                    confirmed_by_present.get(k, 0) / count, 4
                )
                for k, count in sorted(complete_by_present.items())
            },
            "confirmed_change_lag_hours": {
                "min": min(confirmed_lag_hours) if confirmed_lag_hours else None,
                "median": sorted(confirmed_lag_hours)[
                    len(confirmed_lag_hours) // 2
                ] if confirmed_lag_hours else None,
                "max": max(confirmed_lag_hours) if confirmed_lag_hours else None,
            },
            "regime_now_distribution": {
                MarketRegime(k).name: v for k, v in sorted(regime_now_counts.items())
            },
            "regime_48h_distribution": {
                MarketRegime(k).name: v for k, v in sorted(regime_48h_counts.items())
            },
            # backward-compatible key
            "regime_distribution": {
                MarketRegime(k).name: v for k, v in sorted(regime_now_counts.items())
            },
            "message": (
                f"processed {len(candidates) - skipped}: now labels + "
                f"regime_48h set={regime_48h_set}, cleared/missing_future={regime_48h_cleared}"
                if matched > 0
                else "no rows matched for update"
            ),
        }

    def explain(self, feature: Dict[str, Any]) -> Dict[str, Any]:
        regime = self.classify(feature)
        return {
            "source": "rules",
            "role": "present",
            "regime": regime,
            "regime_label": MarketRegime(regime).name,
            "adx_4h": feature.get("adx_4h"),
            "plus_di_4h": feature.get("plus_di_4h"),
            "minus_di_4h": feature.get("minus_di_4h"),
            "atr_ratio_4h_1h": feature.get("atr_ratio_4h_1h"),
            "trend_continuation_4h": feature.get("trend_continuation_4h"),
            "ema_cross_4h_12_26": feature.get("ema_cross_4h_12_26"),
        }
