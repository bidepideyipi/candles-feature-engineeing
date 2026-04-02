"""
Feature type definitions using Pydantic v2.
Provides type safety and validation for feature data.
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class Feature1H(BaseModel):
    """1小时基础特征"""
    close_1h_normalized: float = Field(default=0.0, description="价格标准化")
    volume_1h_normalized: float = Field(default=0.0, description="成交量标准化")
    rsi_14_1h: int = Field(default=50, description="RSI 14周期")
    macd_line_1h: float = Field(default=0.0, description="MACD快线")
    macd_signal_1h: float = Field(default=0.0, description="MACD信号线")
    macd_histogram_1h: float = Field(default=0.0, description="MACD直方图")
    price: float = Field(default=0.0, description="原始价格")
    
    hour_cos: float = Field(default=0.0, description="小时余弦编码")
    hour_sin: float = Field(default=0.0, description="小时正弦编码")
    day_of_week: int = Field(default=0, description="星期几")
    
    upper_shadow_ratio_1h: float = Field(default=0.0, description="上引线比例")
    lower_shadow_ratio_1h: float = Field(default=0.0, description="下引线比例")
    shadow_imbalance_1h: float = Field(default=0.0, description="引线不平衡")
    body_ratio_1h: float = Field(default=0.0, description="实体比例")
    
    atr_1h: float = Field(default=0.0, description="ATR波动率")
    adx_1h: float = Field(default=0.0, description="ADX趋势强度")
    plus_di_1h: float = Field(default=0.0, description="+DI方向指标")
    minus_di_1h: float = Field(default=0.0, description="-DI方向指标")
    ema_12_1h: float = Field(default=0.0, description="EMA 12")
    ema_26_1h: float = Field(default=0.0, description="EMA 26")
    ema_48_1h: float = Field(default=0.0, description="EMA 48")
    ema_cross_1h_12_26: int = Field(default=0, description="EMA 12/26 交叉信号")
    ema_cross_1h_26_48: int = Field(default=0, description="EMA 26/48 交叉信号")
    
    model_config = ConfigDict(extra="ignore")


class Feature15M(BaseModel):
    """15分钟高频特征"""
    rsi_14_15m: int = Field(default=50, description="RSI 14周期")
    volume_impulse_15m: float = Field(default=0.0, description="成交量脉冲")
    macd_line_15m: float = Field(default=0.0, description="MACD快线")
    macd_signal_15m: float = Field(default=0.0, description="MACD信号线")
    macd_histogram_15m: float = Field(default=0.0, description="MACD直方图")
    atr_15m: float = Field(default=0.0, description="ATR波动率")
    stoch_k_15m: float = Field(default=50.0, description="Stochastic K")
    stoch_d_15m: float = Field(default=50.0, description="Stochastic D")
    
    model_config = ConfigDict(extra="ignore")


class Feature4H(BaseModel):
    """4小时中期特征"""
    rsi_14_4h: int = Field(default=50, description="RSI 14周期")
    trend_continuation_4h: float = Field(default=0.0, description="趋势延续强度")
    macd_line_4h: float = Field(default=0.0, description="MACD快线")
    macd_signal_4h: float = Field(default=0.0, description="MACD信号线")
    macd_histogram_4h: float = Field(default=0.0, description="MACD直方图")
    atr_4h: float = Field(default=0.0, description="ATR波动率")
    adx_4h: float = Field(default=0.0, description="ADX趋势强度")
    plus_di_4h: float = Field(default=0.0, description="+DI方向指标")
    minus_di_4h: float = Field(default=0.0, description="-DI方向指标")
    ema_12_4h: float = Field(default=0.0, description="EMA 12")
    ema_26_4h: float = Field(default=0.0, description="EMA 26")
    ema_48_4h: float = Field(default=0.0, description="EMA 48")
    ema_cross_4h_12_26: int = Field(default=0, description="EMA 12/26 交叉信号")
    ema_cross_4h_26_48: int = Field(default=0, description="EMA 26/48 交叉信号")
    
    upper_shadow_ratio_4h: float = Field(default=0.0, description="上引线比例")
    lower_shadow_ratio_4h: float = Field(default=0.0, description="下引线比例")
    shadow_imbalance_4h: float = Field(default=0.0, description="引线不平衡")
    body_ratio_4h: float = Field(default=0.0, description="实体比例")
    
    model_config = ConfigDict(extra="ignore")


class Feature1D(BaseModel):
    """1天长期特征"""
    rsi_14_1d: int = Field(default=50, description="RSI 14周期")
    atr_1d: float = Field(default=0.0, description="ATR波动率")
    bollinger_upper_1d: float = Field(default=0.0, description="布林带上轨")
    bollinger_lower_1d: float = Field(default=0.0, description="布林带下轨")
    bollinger_position_1d: float = Field(default=0.5, description="布林带位置")
    
    upper_shadow_ratio_1d: float = Field(default=0.0, description="上引线比例")
    lower_shadow_ratio_1d: float = Field(default=0.0, description="下引线比例")
    shadow_imbalance_1d: float = Field(default=0.0, description="引线不平衡")
    body_ratio_1d: float = Field(default=0.0, description="实体比例")
    
    macd_line_1d: float = Field(default=0.0, description="MACD快线")
    macd_signal_1d: float = Field(default=0.0, description="MACD信号线")
    
    model_config = ConfigDict(extra="ignore")


class FeatureBase(BaseModel):
    """特征基础字段"""
    timestamp: int = Field(default=0, description="时间戳(毫秒)")
    inst_id: str = Field(default="ETH-USDT-SWAP", description="交易对")
    bar: str = Field(default="1H", description="时间周期")
    label: Optional[int] = Field(default=None, description="标签(收盘价波动)")
    label_high: Optional[int] = Field(default=None, description="标签(高点波动)")
    label_low: Optional[int] = Field(default=None, description="标签(低点波动)")


class Feature(FeatureBase, Feature1H, Feature15M, Feature4H, Feature1D):
    """完整特征数据模型"""
    
    model_config = ConfigDict(
        extra="ignore",  # 忽略 MongoDB 额外字段
        populate_by_name=True,  # 允许按字段名填充
    )
    
    def to_dict(self) -> dict:
        """转换为字典，兼容 MongoDB 存储"""
        return self.model_dump(mode='json', exclude_none=False)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Feature':
        """从字典创建，兼容 MongoDB 查询"""
        return cls.model_validate(data)


class FeatureCreate(BaseModel):
    """特征创建模型（用于特征生成时）"""
    timestamp: int
    inst_id: str = "ETH-USDT-SWAP"
    bar: str = "1H"
    
    close_1h_normalized: float = 0.0
    volume_1h_normalized: float = 0.0
    rsi_14_1h: int = 50
    macd_line_1h: float = 0.0
    macd_signal_1h: float = 0.0
    macd_histogram_1h: float = 0.0
    price: float = 0.0
    hour_cos: float = 0.0
    hour_sin: float = 0.0
    day_of_week: int = 0
    upper_shadow_ratio_1h: float = 0.0
    lower_shadow_ratio_1h: float = 0.0
    shadow_imbalance_1h: float = 0.0
    body_ratio_1h: float = 0.0
    
    rsi_14_15m: int = 50
    volume_impulse_15m: float = 0.0
    macd_line_15m: float = 0.0
    macd_signal_15m: float = 0.0
    macd_histogram_15m: float = 0.0
    atr_15m: float = 0.0
    stoch_k_15m: float = 50.0
    stoch_d_15m: float = 50.0
    
    rsi_14_4h: int = 50
    trend_continuation_4h: float = 0.0
    macd_line_4h: float = 0.0
    macd_signal_4h: float = 0.0
    macd_histogram_4h: float = 0.0
    atr_4h: float = 0.0
    adx_4h: float = 0.0
    plus_di_4h: float = 0.0
    minus_di_4h: float = 0.0
    ema_12_4h: float = 0.0
    ema_26_4h: float = 0.0
    ema_48_4h: float = 0.0
    ema_cross_4h_12_26: int = 0
    ema_cross_4h_26_48: int = 0
    upper_shadow_ratio_4h: float = 0.0
    lower_shadow_ratio_4h: float = 0.0
    shadow_imbalance_4h: float = 0.0
    body_ratio_4h: float = 0.0
    
    rsi_14_1d: int = 50
    atr_1d: float = 0.0
    bollinger_upper_1d: float = 0.0
    bollinger_lower_1d: float = 0.0
    bollinger_position_1d: float = 0.5
    upper_shadow_ratio_1d: float = 0.0
    lower_shadow_ratio_1d: float = 0.0
    shadow_imbalance_1d: float = 0.0
    body_ratio_1d: float = 0.0
    
    model_config = ConfigDict(extra="ignore")
    
    def to_feature(self) -> Feature:
        """转换为 Feature 模型"""
        return Feature(**self.model_dump())
