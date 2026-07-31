"""Regime API: 拉取 / 统计 / 标注 / 训练 / 预测 / 一键流水线。"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from collect.candlestick_continuity import DEFAULT_BARS, candlestick_continuity_checker
from collect.candlestick_handler import candlestick_handler
from collect.okex_fetcher import okex_fetcher
from config.settings import config
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
    """
    查看 feature / regime_label 覆盖，以及各周期 K 线数量。
    （原 /fetch/0-history-count 已并入 candlestick_counts。）
    """
    from collect.feature_handler import feature_handler

    total = feature_handler.count_features(inst_id=inst_id, bar=bar)
    labeled = feature_handler.count_regime_labeled(inst_id=inst_id, bar=bar)
    candlestick_counts = {
        b: candlestick_handler.count(inst_id=inst_id, bar=b) for b in DEFAULT_BARS
    }
    return {
        "inst_id": inst_id,
        "bar": bar,
        "total_features": total,
        "regime_labeled": labeled,
        "regime_unlabeled": max(0, total - labeled),
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
    if config.PRODUCTION_MODE:
        raise HTTPException(status_code=403, detail="Disabled in production mode")

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
    if config.PRODUCTION_MODE:
        raise HTTPException(status_code=403, detail="Disabled in production mode")
    return candlestick_continuity_checker.check_all(inst_id=inst_id, limit=limit)


@router.get("/pipeline")
def run_regime_pipeline(
    inst_id: str = "ETH-USDT-SWAP",
    max_records_1h: int = Query(2400, ge=100, le=10000),
    skip_pull: bool = False,
    strict_continuity: bool = True,
    merge_limit: int = Query(5000, ge=1, le=200000),
    label_limit: int = Query(50000, ge=1, le=200000),
    only_fix_none_label: bool = True,
    train_limit: int = Query(10000, ge=200, le=200000),
    test_ratio: float = Query(0.2, ge=0.05, le=0.5),
) -> Dict[str, Any]:
    """
    Regime 一键流水线：拉取多周期 K 线 → 连续性校验 → 合并特征 →
    regime 标注 → 训练 → 返回聚合报告（summary）。

    推荐：开发环境一次跑通训练。
    - skip_pull=true：跳过 OKX 拉取，用已有 Mongo 数据
    - strict_continuity=true（默认）：任一周期有缺口则中止，避免脏特征
    """
    if config.PRODUCTION_MODE:
        raise HTTPException(status_code=403, detail="Disabled in production mode")

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
) -> Dict[str, Any]:
    """
    用规则引擎为 feature 打 regime_label（1=TREND_UP, 2=TREND_DOWN, 3=RANGE）。
    - only_fix_none=true：仅标注尚无 regime_label 的记录
    - only_fix_none=false：全量重标注（所有 feature）
    需先有 feature（可通过 /regime/pipeline 生成）。
    """
    if config.PRODUCTION_MODE:
        raise HTTPException(status_code=403, detail="Disabled in production mode")

    labeler = RegimeLabeler()
    return labeler.loop(inst_id=inst_id, only_fix_none=only_fix_none, limit=limit)


@router.get("/2-train")
def train_regime_model(
    inst_id: str = "ETH-USDT-SWAP",
    limit: int = 10000,
    test_ratio: float = 0.2,
) -> Dict[str, Any]:
    """
    训练 regime XGBoost 三分类模型（时间序列切分，非随机 shuffle）。
    需先执行 /regime/1-label。
    """
    if config.PRODUCTION_MODE:
        raise HTTPException(status_code=403, detail="Disabled in production mode")

    try:
        results = regime_trainer.train_model(
            inst_id=inst_id, limit=limit, test_ratio=test_ratio
        )
        return {"success": True, **results}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/3-predict")
def predict_regime(from_local: bool = True) -> Dict[str, Any]:
    """
    预测当前市场 regime，并推荐策略（default / grid）。
    Redis：始终 SET 当前趋势；仅当滑动窗口检测到 UP↔DOWN 反转时才 XADD 告警。
    生产环境可用。
    """
    if not regime_trainer.load_model():
        raise HTTPException(
            status_code=404,
            detail="Regime model not found. Run /regime/2-train first.",
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
