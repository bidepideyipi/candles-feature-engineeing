"""
基于已有技术指标特征，规则标注当前市场 regime（ground truth）。
标签表示「当前时刻」的市场结构，不预测未来涨跌。
"""
import logging
from typing import Any, Dict

from regime.regime_types import MarketRegime

log = logging.getLogger(__name__)


class RegimeLabeler:
    ADX_TREND_THRESHOLD = 20.0
    ADX_RANGE_THRESHOLD = 18.0
    ATR_RATIO_RANGE_MAX = 0.85
    TREND_CONT_THRESHOLD = 0.0

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

    def loop(
        self, inst_id: str, limit: int = 50000, only_fix_none: bool = True, bar: str = "1H"
    ) -> Dict[str, Any]:
        from collect.feature_handler import feature_handler

        total_in_db = feature_handler.count_features(inst_id=inst_id, bar=bar)
        labeled_before = feature_handler.count_regime_labeled(inst_id=inst_id, bar=bar)

        if only_fix_none:
            features = feature_handler.get_features_without_regime(
                inst_id=inst_id, bar=bar, limit=limit
            )
        else:
            features = feature_handler.get_all_features(
                inst_id=inst_id, bar=bar, limit=limit
            )

        if not features:
            log.warning("无 feature 可标注 regime, inst_id=%s bar=%s", inst_id, bar)
            return {
                "success": False,
                "inst_id": inst_id,
                "bar": bar,
                "only_fix_none": only_fix_none,
                "total_in_db": total_in_db,
                "labeled_before": labeled_before,
                "processed": 0,
                "matched": 0,
                "modified": 0,
                "unchanged": 0,
                "message": "未找到可处理的 feature，请先执行 /fetch/3-merge-feature",
            }

        matched = 0
        modified = 0
        unchanged = 0
        regime_counts: Dict[int, int] = {}

        for feature in features:
            regime = self.classify(feature)
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
            ts = feature.get("timestamp")
            result = feature_handler.update_regime_label(
                inst_id, ts, regime, bar=bar
            )
            if result["matched"] > 0:
                matched += 1
                if result["modified"] > 0:
                    modified += 1
                else:
                    unchanged += 1

        labeled_after = feature_handler.count_regime_labeled(inst_id=inst_id, bar=bar)

        log.info(
            "regime 标注 inst_id=%s processed=%s matched=%s modified=%s unchanged=%s",
            inst_id, len(features), matched, modified, unchanged,
        )

        return {
            "success": matched > 0,
            "inst_id": inst_id,
            "bar": bar,
            "only_fix_none": only_fix_none,
            "total_in_db": total_in_db,
            "labeled_before": labeled_before,
            "labeled_after": labeled_after,
            "processed": len(features),
            "matched": matched,
            "modified": modified,
            "unchanged": unchanged,
            "regime_distribution": {
                MarketRegime(k).name: v for k, v in sorted(regime_counts.items())
            },
            "message": (
                f"处理 {len(features)} 条，新写入/变更 {modified} 条，值未变 {unchanged} 条"
                if matched > 0
                else "有 feature 但未能匹配更新，请检查 inst_id/timestamp/bar"
            ),
        }

    def explain(self, feature: Dict[str, Any]) -> Dict[str, Any]:
        regime = self.classify(feature)
        return {
            "regime": regime,
            "regime_label": MarketRegime(regime).name,
            "adx_4h": feature.get("adx_4h"),
            "plus_di_4h": feature.get("plus_di_4h"),
            "minus_di_4h": feature.get("minus_di_4h"),
            "atr_ratio_4h_1h": feature.get("atr_ratio_4h_1h"),
            "trend_continuation_4h": feature.get("trend_continuation_4h"),
            "ema_cross_4h_12_26": feature.get("ema_cross_4h_12_26"),
        }
