"""Regime (Option C) API: 标注 / 训练 / 预测市场结构。"""
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from config.settings import config
from feature.feature_merge import FeatureMerge
from models.regime_trainer import regime_trainer
from regime.regime_labeler import RegimeLabeler
from stream.redis_stream_handler import redis_stream_handler

router = APIRouter(prefix="/regime", tags=["regime"])


@router.get("/0-stats")
def regime_stats(inst_id: str = "ETH-USDT-SWAP", bar: str = "1H") -> Dict[str, Any]:
    """查看 feature 总量与 regime_label 覆盖情况。"""
    from collect.feature_handler import feature_handler

    total = feature_handler.count_features(inst_id=inst_id, bar=bar)
    labeled = feature_handler.count_regime_labeled(inst_id=inst_id, bar=bar)
    return {
        "inst_id": inst_id,
        "bar": bar,
        "total_features": total,
        "regime_labeled": labeled,
        "regime_unlabeled": max(0, total - labeled),
    }


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
    需先完成 /fetch/3-merge-feature。
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
    生产环境可用。
    """
    if not regime_trainer.load_model():
        raise HTTPException(status_code=404, detail="Regime model not found. Run /regime/2-train first.")

    feature_merge = FeatureMerge()
    features = (
        feature_merge.quick_process_eth_from_mongodb()
        if from_local
        else feature_merge.quick_process_eth()
    )
    if features is None:
        raise HTTPException(status_code=404, detail="Failed to extract features")

    payload = regime_trainer.build_prediction_payload(features)
    redis_stream_handler.publish_regime(payload)
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
