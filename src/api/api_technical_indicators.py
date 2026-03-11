from api.model import TechnicalIndicatorsResponse, TechnicalIndicatorsModel
from fastapi import FastAPI, HTTPException, APIRouter
from models.xgboost_trainer import xgb_trainer
import time

router = APIRouter(prefix="/technical", tags=["technical"])

@router.post("/0", response_model=TechnicalIndicatorsResponse)
async def receive_technical_indicators(data: TechnicalIndicatorsModel):
    """
    接收技术指标数据并进行初步分析
    """
    if not xgb_trainer.load_model():
        raise HTTPException(status_code=404, detail="Failed to load model. Please train the model first.")
    
    prediction, probabilities = xgb_trainer.predict_single(data.dict())
        
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
         
    # 分析信号
    analysis = {
        "market_condition": analyze_market_condition(data),
        "signals": generate_signals(data),
        "risk_level": calculate_risk_level(data),
        "confidence_score": calculate_confidence(data),
        "prediction": int(prediction),
        "prediction_label": class_labels.get(prediction, f"类别 {prediction}"),
        "probabilities": prob_dict,
        "features_count": len(xgb_trainer.feature_columns),
        "inst_id": "ETH-USDT-SWAP"
    }
    
    return TechnicalIndicatorsResponse(
        success=True,
        message="技术指标接收成功",
        data=data,
        timestamp=int(time.time() * 1000),
        analysis=analysis
    )


def analyze_market_condition(data: TechnicalIndicatorsModel) -> str:
    """分析市场状态"""
    if data.is_rsi_oversold_1h and data.is_rsi_oversold_4h:
        return "超卖区域"
    elif data.is_rsi_overbought_1h and data.is_rsi_overbought_4h:
        return "超买区域"
    elif data.trend_continuation_4h == 1 and data.adx_4h > 25:
        return "强趋势"
    elif data.adx_4h < 20:
        return "震荡市"
    return "中性"


def generate_signals(data: TechnicalIndicatorsModel) -> dict:
    """生成交易信号"""
    signals = {
        "buy_signals": [],
        "sell_signals": [],
        "neutral_signals": []
    }
    
    # 买入信号
    if data.is_rsi_oversold_1h and data.macd_histogram_1h > 0:
        signals["buy_signals"].append("1小时RSI超卖且MACD转正")
    
    if data.ema_cross_4h_12_26 == 1:
        signals["buy_signals"].append("4小时EMA金叉")
    
    if data.bollinger_position_1d < 0.2:
        signals["buy_signals"].append("日线布林带下轨附近")
    
    # 卖出信号
    if data.is_rsi_overbought_1h and data.macd_histogram_1h < 0:
        signals["sell_signals"].append("1小时RSI超买且MACD转负")
    
    if data.ema_cross_4h_12_26 == 0 and data.ema_cross_4h_26_48 == 0:
        signals["sell_signals"].append("4小时EMA死叉")
    
    if data.bollinger_position_1d > 0.8:
        signals["sell_signals"].append("日线布林带上轨附近")
    
    return signals


def calculate_risk_level(data: TechnicalIndicatorsModel) -> str:
    """计算风险等级"""
    risk_score = 0
    
    # 波动率评分
    if data.atr_1d > 200:
        risk_score += 2
    elif data.atr_1d > 100:
        risk_score += 1
    
    # 趋势强度评分
    if data.adx_4h < 20:
        risk_score += 1  # 震荡市风险较高
    
    # 位置评分
    if data.is_bollinger_extreme_1d:
        risk_score += 1
    
    if risk_score >= 3:
        return "高风险"
    elif risk_score >= 2:
        return "中风险"
    return "低风险"


def calculate_confidence(data: TechnicalIndicatorsModel) -> float:
    """计算置信度评分(0-1)"""
    confidence = 0.5
    
    # 多时间周期一致性加分
    if (data.is_rsi_oversold_1h and data.is_rsi_oversold_4h) or \
       (data.is_rsi_overbought_1h and data.is_rsi_overbought_4h):
        confidence += 0.2
    
    # 趋势明确加分
    if data.adx_4h > 25:
        confidence += 0.15
    
    # 成交量确认加分
    if data.volume_impulse_15m > 0.5:
        confidence += 0.1
    
    return min(confidence, 1.0)