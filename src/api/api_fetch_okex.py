from fastapi import APIRouter, HTTPException
from collect.okex_fetcher import okex_fetcher
from collect.candlestick_handler import candlestick_handler
import pandas as pd
import numpy as np
from collect.normalization_handler import normalization_handler
from collect.feature_handler import feature_handler
from utils.normalize_encoder import NORMALIZED
from feature.feature_merge import FeatureMerge
from feature.feature_label import FeatureLabel
from config.settings import config
from models.xgboost_trainer import xgb_trainer
from typing import Dict, Any

# Create router for OKEx fetching endpoints
router = APIRouter(prefix="/fetch", tags=["fetch"])

@router.get("/0-history-count")
def get_history_count(inst_id: str = "ETH-USDT-SWAP", bar: str = "1H"):
    """
    获取历史数据数量
    """
    if config.PRODUCTION_MODE:
        raise HTTPException(status_code=403, detail="This endpoint is disabled in production mode")
    
    count = candlestick_handler.count(inst_id=inst_id, bar=bar)
    if count is None:
        raise HTTPException(status_code=404, detail="No data found")
    return {
        "inst_id": inst_id,
        "bar": bar,
        "count": count
    }
        
@router.get("/1-pull-history")
def fetch_okex_data(
    inst_id: str = "ETH-USDT-SWAP",
    bar: str = "1H",
    max_records: int = 600,
    current_after: int = None
):
    """
    Fetch history candlestick data from OKEx API.
    
    系统的第一步是从OKEx拉取数据，这是第一个要请求的接口。
    由于拉取数据是一个耗时的操作，而且是历史数据，所以还主要用于训练数据的采集。
    拉取的数据如4H是600条，那么1H就是600*4=2400条。15m就是600*4*4=9600条。
    
    Args:
        inst_id: Instrument ID (e.g., ETH-USDT-SWAP)
        bar: Time interval (e.g., "15m", "1H", "4H", "1D")
        max_records: Number of records to fetch (max 100000)
        current_after: 时间戳，毫秒级
    
    Returns:
        Candlestick data from OKEx
    """
    if config.PRODUCTION_MODE:
        raise HTTPException(status_code=403, detail="This endpoint is disabled in production mode")
    
    try:
        # Validate parameters
        if max_records < 600 or max_records > 60000:
            raise HTTPException(status_code=400, detail="max_records must be between 600 and 60000")
        
        if bar not in ["15m", "1H", "4H", "1D"]:
            raise HTTPException(status_code=400, detail="Invalid bar parameter")
        
        # Fetch data from OKEx
        success = okex_fetcher.fetch_historical_data(inst_id=inst_id, bar=bar, max_records=max_records, current_after=current_after)
        
        if not success:
            raise HTTPException(status_code=404, detail="No data found")
        
        return {
            "inst_id": inst_id,
            "bar": bar,
            "max_records": max_records,
            "success": success
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")

@router.get("/2-normalize")
def normalize_data(inst_id: str = "ETH-USDT-SWAP", bar: str = "1H", limit: int = 5000):
    """
    归一化数据
    
    系统的第二步是对数据进行归一化，这是第二个要请求的接口。
    归一化的目的是将数据转换为0到1之间的范围，这在很多机器学习算法中都是必要的。
    """
    if config.PRODUCTION_MODE:
        raise HTTPException(status_code=403, detail="This endpoint is disabled in production mode")
    
    candles = candlestick_handler.get_candlestick_data(inst_id = inst_id, bar = bar, limit = limit)
        
    close = pd.Series(item['close'] for item in candles)
    volume = pd.Series(item['volume'] for item in candles)
    assert close is not None
    assert volume is not None
    _, mean_close, std = NORMALIZED.calculate(close)
    _, mean_volume, std_volume  = NORMALIZED.calculate(volume)
    is_close_saved = normalization_handler.save_normalization_params(inst_id = inst_id, bar = bar, column = 'close', mean = mean_close, std = std)
    is_volume_saved = normalization_handler.save_normalization_params(inst_id = inst_id, bar = bar, column = 'volume', mean = mean_volume, std = std_volume)
    success = is_close_saved and is_volume_saved
    if not success:
        raise HTTPException(status_code=404, detail="No data found")
    return {
        "inst_id": inst_id,
        "bar": bar,
        "success": success
    }
    
@router.get("/3-merge-feature")
def merge_feature(limit: int = 5000, before: int = None):
    """
    合并特征
    
    系统的第三步是合并特征，这是第三个要请求的接口。
    合并特征的目的是将归一化后的数据合并到一个DataFrame中，这在很多机器学习算法中都是必要的。
    """
    if config.PRODUCTION_MODE:
        raise HTTPException(status_code=403, detail="This endpoint is disabled in production mode")
    
    feature_merge = FeatureMerge()
    feature_merge.loop(limit=limit, before=before)
    return {
        "limit": limit,
        "success": True
    }

@router.get("/4-lable")
def merge_label(inst_id: str = "ETH-USDT-SWAP", onlyFixNone: bool = True):
    """
    合并标签
    
    系统的第四步是合并标签，这是第四个要请求的接口。
    合并标签的目的是将归一化后的数据合并到一个DataFrame中，这在很多机器学习算法中都是必要的。
    onlyFixNone = True 表示只修复 None 值，而不添加新的标签；False 者会把所有标签重新更新，用于分类计算方式被调整的情况
    """
    if config.PRODUCTION_MODE:
        raise HTTPException(status_code=403, detail="This endpoint is disabled in production mode")
    
    feature_label = FeatureLabel()
    feature_label.loop(inst_id=inst_id, limit=200000, onlyFixNone=onlyFixNone)
    
    return {
        "inst_id": inst_id,
        "onlyFixNone": onlyFixNone,
        "success": True
    }

@router.get("/5-predict")
def predict_price_movement(fromLocal: bool = True) -> Dict[str, Any]:
    """
    预测价格走势
    
    系统的第五步是使用训练好的模型进行预测，这是第五个要请求的接口。
    使用实时 K 线数据计算特征，然后使用模型进行预测。
    
    返回 5 类模型的预测结果。
    
    Returns:
        {
            "timestamp": int,
            "prediction": int,
            "prediction_label": str,
            "probabilities": {1: float, 2: float, 3: float, 4: float, 5: float},
            "inst_id": str
        }
    """
    try:
        if not xgb_trainer.load_model():
            raise HTTPException(status_code=404, detail="Failed to load model. Please train the model first.")
        
        feature_merge = FeatureMerge()
        if fromLocal:
            features = feature_merge.quick_process_eth_from_mongodb()
        else:
            features = feature_merge.quick_process_eth()
        
        if features is None:
            raise HTTPException(status_code=404, detail="Failed to extract features from realtime data")
        
        prediction, probabilities = xgb_trainer.predict_single(features)
        
        class_labels = {
            1: "暴跌 (<-3.6%)",
            2: "下跌 (-3.6% ~ -1.2%)",
            3: "横盘 (-1.2% ~ 1.2%)",
            4: "上涨 (1.2% ~ 3.6%)",
            5: "暴涨 (>3.6%)"
        }
        
        prob_dict = {}
        for i, prob in enumerate(probabilities):
            class_num = i + 1
            prob_dict[class_num] = round(float(prob), 4)
        
        return {
            "timestamp": features.get("timestamp"),
            "prediction": int(prediction),
            "prediction_label": class_labels.get(prediction, f"类别 {prediction}"),
            "probabilities": prob_dict,
            "features_count": len(xgb_trainer.feature_columns),
            "inst_id": "ETH-USDT-SWAP"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

