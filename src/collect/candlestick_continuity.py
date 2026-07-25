"""
校验各时间维度 K 线时间戳是否按固定周期连续（无缺口）。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from collect.candlestick_handler import candlestick_handler

logger = logging.getLogger(__name__)

BAR_INTERVAL_MS = {
    "15m": 15 * 60 * 1000,
    "1H": 60 * 60 * 1000,
    "4H": 4 * 60 * 60 * 1000,
    "1D": 24 * 60 * 60 * 1000,
}

DEFAULT_BARS = ("15m", "1H", "4H", "1D")
# 报告里最多列出的缺口样例数
MAX_GAP_SAMPLES = 20


class CandlestickContinuityChecker:
    """扫描 MongoDB candlesticks，检测相邻 K 线间隔是否等于预期 bar 周期。"""

    def check_bar(
        self,
        inst_id: str,
        bar: str,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        if bar not in BAR_INTERVAL_MS:
            return {
                "bar": bar,
                "ok": False,
                "error": f"不支持的 bar: {bar}",
                "count": 0,
                "gap_count": 0,
                "gaps": [],
            }

        interval = BAR_INTERVAL_MS[bar]
        timestamps = self._load_timestamps(inst_id=inst_id, bar=bar, limit=limit)
        count = len(timestamps)

        if count == 0:
            return {
                "bar": bar,
                "ok": False,
                "error": "无数据",
                "count": 0,
                "expected_interval_ms": interval,
                "earliest_ts": None,
                "latest_ts": None,
                "gap_count": 0,
                "gaps": [],
                "coverage_ratio": 0.0,
            }

        gaps: List[Dict[str, Any]] = []
        missing_bars = 0
        for i in range(len(timestamps) - 1):
            delta = timestamps[i + 1] - timestamps[i]
            if delta == interval:
                continue
            miss = max(0, int(delta // interval) - 1) if delta > interval else 0
            missing_bars += miss
            if len(gaps) < MAX_GAP_SAMPLES:
                gaps.append(
                    {
                        "index": i,
                        "from_ts": timestamps[i],
                        "to_ts": timestamps[i + 1],
                        "delta_ms": delta,
                        "expected_ms": interval,
                        "missing_bars": miss if delta > interval else 0,
                        "duplicate_or_shrink": delta < interval,
                    }
                )

        span = timestamps[-1] - timestamps[0]
        expected_count = (span // interval) + 1 if span >= 0 else count
        coverage_ratio = (
            round(count / expected_count, 4) if expected_count > 0 else 0.0
        )

        return {
            "bar": bar,
            "ok": len(gaps) == 0,
            "error": f"{len(gaps)} 处不连续" if gaps else None,
            "count": count,
            "expected_interval_ms": interval,
            "earliest_ts": timestamps[0],
            "latest_ts": timestamps[-1],
            "gap_count": len(gaps),
            "missing_bars_estimate": missing_bars,
            "gaps": gaps,
            "gaps_truncated": len(gaps) >= MAX_GAP_SAMPLES,
            "coverage_ratio": coverage_ratio,
            "expected_count_by_span": int(expected_count),
        }

    def check_all(
        self,
        inst_id: str = "ETH-USDT-SWAP",
        bars: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        bars = list(bars or DEFAULT_BARS)
        by_bar: Dict[str, Any] = {}
        for bar in bars:
            by_bar[bar] = self.check_bar(inst_id=inst_id, bar=bar, limit=limit)

        ok = all(v.get("ok") for v in by_bar.values())
        failed_bars = [b for b, v in by_bar.items() if not v.get("ok")]

        return {
            "inst_id": inst_id,
            "ok": ok,
            "failed_bars": failed_bars,
            "bars": by_bar,
            "message": (
                "全部时间维度连续"
                if ok
                else f"不连续: {', '.join(failed_bars)}"
            ),
        }

    def _load_timestamps(
        self, inst_id: str, bar: str, limit: Optional[int]
    ) -> List[int]:
        """按升序加载 timestamp；limit 时取最近 limit 根再升序。"""
        collection = candlestick_handler._get_collection()
        if collection is None:
            return []

        query = {"inst_id": inst_id, "bar": bar}
        try:
            if limit and limit > 0:
                cursor = (
                    collection.find(query, {"timestamp": 1, "_id": 0})
                    .sort("timestamp", -1)
                    .limit(limit)
                )
                ts = sorted(int(d["timestamp"]) for d in cursor if "timestamp" in d)
            else:
                cursor = collection.find(query, {"timestamp": 1, "_id": 0}).sort(
                    "timestamp", 1
                )
                ts = [int(d["timestamp"]) for d in cursor if "timestamp" in d]
            return ts
        except Exception as e:
            logger.error("加载 timestamp 失败 inst_id=%s bar=%s: %s", inst_id, bar, e)
            return []


candlestick_continuity_checker = CandlestickContinuityChecker()
