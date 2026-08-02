"""Regime API: 拉取 / 统计 / 标注 / 训练 / 预测 / 一键流水线。"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from collect.candlestick_continuity import DEFAULT_BARS, candlestick_continuity_checker
from collect.candlestick_handler import candlestick_handler
from collect.okex_fetcher import okex_fetcher
from feature.feature_merge import FeatureMerge
from models.regime_trainer import regime_trainer
from regime.regime_labeler import RegimeLabeler
from regime.regime_pipeline import regime_pipeline
from stream.redis_stream_handler import redis_stream_handler

router = APIRouter(prefix="/regime", tags=["regime"])


@router.get("/0-stats")
def regime_stats(
    inst_id: str = "ETH-USDT-SWAP",
    bar: str = "1H",
) -> Dict[str, Any]:
    """Feature coverage for present (regime_now) and forward (regime_48h) labels."""
    from collect.feature_handler import feature_handler

    total = feature_handler.count_features(inst_id=inst_id, bar=bar)
    labeled_now = feature_handler.count_regime_labeled(inst_id=inst_id, bar=bar)
    labeled_48h = feature_handler.count_regime_48h_labeled(inst_id=inst_id, bar=bar)
    candlestick_counts = {
        b: candlestick_handler.count(inst_id=inst_id, bar=b) for b in DEFAULT_BARS
    }
    return {
        "inst_id": inst_id,
        "bar": bar,
        "total_features": total,
        "regime_now_labeled": labeled_now,
        "regime_now_unlabeled": max(0, total - labeled_now),
        "regime_48h_labeled": labeled_48h,
        "regime_48h_unlabeled": max(0, total - labeled_48h),
        # backward-compatible aliases
        "regime_labeled": labeled_now,
        "regime_unlabeled": max(0, total - labeled_now),
        "candlestick_counts": candlestick_counts,
    }


@router.get("/pull-history")
def pull_history(
    inst_id: str = "ETH-USDT-SWAP",
    bar: str = "1H",
    max_records: int = 600,
    current_after: Optional[int] = None,
) -> Dict[str, Any]:
    """
    从 OKEx 拉取历史 K 线并写入 MongoDB（原 /fetch/1-pull-history）。

    条数参考：4H=600 时，同跨度约 1H=2400、15m=9600、1D≈100。
    单次 max_records 上限 10000。
    """
    try:
        if max_records < 1 or max_records > 10000:
            raise HTTPException(
                status_code=400, detail="max_records must be between 1 and 10000"
            )
        if bar not in list(DEFAULT_BARS):
            raise HTTPException(status_code=400, detail="Invalid bar parameter")

        success = okex_fetcher.fetch_historical_data(
            inst_id=inst_id,
            bar=bar,
            max_records=max_records,
            current_after=current_after,
        )
        if not success:
            raise HTTPException(status_code=404, detail="No data found")

        return {
            "inst_id": inst_id,
            "bar": bar,
            "max_records": max_records,
            "success": success,
            "count": candlestick_handler.count(inst_id=inst_id, bar=bar),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {e}") from e


@router.get("/check-continuity")
def check_continuity(
    inst_id: str = "ETH-USDT-SWAP",
    limit: Optional[int] = Query(
        None, description="仅检查最近 N 根；默认全量"
    ),
) -> Dict[str, Any]:
    """
    检查 15m / 1H / 4H / 1D K 线是否按周期连续。
    替代手工查库验缺口；流水线在 strict 模式下也会调用。
    """
    return candlestick_continuity_checker.check_all(inst_id=inst_id, limit=limit)


@router.get("/merge-features")
def merge_features(
    limit: int = Query(5000, ge=1, le=200000),
    before: Optional[int] = Query(
        None,
        description="Optional 1H candle timestamp (ms); default = latest in Mongo",
    ),
) -> Dict[str, Any]:
    """
    Candlesticks → 1H feature rows (multi-TF indicators + rolling normalize).

    Requires Mongo candlesticks for 15m / 1H / 4H / 1D (pull + continuity first).
    Stepwise order: pull-history → check-continuity → **merge-features** →
    1-label → 2-train. Also runs inside `/regime/pipeline`.
    """
    from collect.feature_handler import feature_handler

    feature_merge = FeatureMerge()
    stats = feature_merge.loop(before=before, limit=limit)
    stats["features_in_db"] = feature_handler.count_features(
        inst_id=feature_merge.inst_id, bar="1H"
    )
    if not stats.get("success"):
        raise HTTPException(
            status_code=400,
            detail=stats.get("last_error") or "Feature merge failed",
        )
    return stats


@router.get("/pipeline")
def run_regime_pipeline(
    inst_id: str = "ETH-USDT-SWAP",
    max_records_1h: int = Query(2400, ge=100, le=10000),
    skip_pull: bool = False,
    strict_continuity: bool = True,
    merge_limit: int = Query(20000, ge=1, le=200000),
    label_limit: int = Query(50000, ge=1, le=200000),
    only_fix_none_label: bool = True,
    train_limit: int = Query(10000, ge=200, le=200000),
    test_ratio: float = Query(0.2, ge=0.05, le=0.5),
) -> Dict[str, Any]:
    """
    One-shot: pull → continuity → merge-features → dual label → train → summary.

    - skip_pull=true: use existing Mongo candlesticks
    - strict_continuity=true (default): abort on any bar gap
    """
    try:
        return regime_pipeline.run(
            inst_id=inst_id,
            max_records_1h=max_records_1h,
            skip_pull=skip_pull,
            strict_continuity=strict_continuity,
            merge_limit=merge_limit,
            label_limit=label_limit,
            only_fix_none_label=only_fix_none_label,
            train_limit=train_limit,
            test_ratio=test_ratio,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}") from e


@router.get("/1-label")
def label_regime(
    inst_id: str = "ETH-USDT-SWAP",
    only_fix_none: bool = True,
    limit: int = 50000,
    horizon_hours: Optional[int] = Query(
        None,
        ge=1,
        le=168,
        description="Forward label horizon in 1H bars (default: REGIME_HORIZON_HOURS)",
    ),
) -> Dict[str, Any]:
    """
    Dual-track labels on 1H features:
    - regime_now: rules at T (present)
    - regime_48h: rules at T+horizon (Mongo field name kept; horizon configurable)
    Changing horizon requires only_fix_none=false to rewrite forward labels.
    """
    labeler = RegimeLabeler(horizon_hours=horizon_hours)
    return labeler.loop(inst_id=inst_id, only_fix_none=only_fix_none, limit=limit)


@router.get("/2-train")
def train_regime_model(
    inst_id: str = "ETH-USDT-SWAP",
    limit: int = 10000,
    test_ratio: float = 0.2,
    class_weight: Optional[str] = Query(
        None,
        description="balanced (default from env) | none",
    ),
    horizon_hours: Optional[int] = Query(
        None,
        ge=1,
        le=168,
        description="Must match labeling horizon used for regime_48h",
    ),
    holdout_start_ts: Optional[int] = Query(
        None,
        ge=1,
        description="Optional fixed holdout start (ms) for fair horizon comparisons",
    ),
) -> Dict[str, Any]:
    """
    Train XGBoost binary continue/change:
    change := regime_fwd != regime_now over horizon.
    Beats always-CONTINUE baseline is the primary gate.
    """
    try:
        results = regime_trainer.train_model(
            inst_id=inst_id,
            limit=limit,
            test_ratio=test_ratio,
            class_weight=class_weight,
            horizon_hours=horizon_hours,
            holdout_start_ts=holdout_start_ts,
        )
        return {"success": True, **results}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/3-predict")
def predict_regime(from_local: bool = True) -> Dict[str, Any]:
    """
    Dual-track:
    - present: rules (now)
    - transition / derived: model P(change) over horizon
    Redis zwin still tracks present UP↔DOWN reversals.
    """
    if not regime_trainer.load_model():
        raise HTTPException(
            status_code=404,
            detail="Continue/change model not found. Run /regime/2-train first.",
        )

    feature_merge = FeatureMerge()
    features = (
        feature_merge.quick_process_eth_from_mongodb()
        if from_local
        else feature_merge.quick_process_eth()
    )
    if features is None:
        raise HTTPException(status_code=404, detail="Failed to extract features")

    payload = regime_trainer.build_prediction_payload(features)
    redis_meta = redis_stream_handler.publish_regime(payload)
    payload["redis"] = redis_meta
    return payload


@router.get("/explain-rules")
def explain_rules(from_local: bool = True) -> Dict[str, Any]:
    """查看规则引擎对当前行情的 regime 判断（不依赖 ML 模型）。"""
    feature_merge = FeatureMerge()
    features = (
        feature_merge.quick_process_eth_from_mongodb()
        if from_local
        else feature_merge.quick_process_eth()
    )
    if features is None:
        raise HTTPException(status_code=404, detail="Failed to extract features")

    labeler = RegimeLabeler()
    feature_dict = features.to_dict() if hasattr(features, "to_dict") else features
    return labeler.explain(feature_dict)
