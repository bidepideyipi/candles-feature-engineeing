from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from enum import Enum

class TimeFrame(str, Enum):
    """时间周期枚举"""
    H1 = "1H"
    M15 = "15M"
    H4 = "4H"
    D1 = "1D"

class InstrumentType(str, Enum):
    """交易对类型枚举"""
    SPOT = "SPOT"
    SWAP = "SWAP"
    FUTURES = "FUTURES"

class TechnicalIndicatorsModel(BaseModel):
    """
    技术指标数据模型
    用于接收和分析多个时间周期的技术指标
    """
    
    # ==== 1H 周期指标 ====
    close_1h_normalized: float = Field(
        ...,
        description="1小时收盘价归一化值",
        ge=-5.0,
        le=5.0
    )
    volume_1h_normalized: float = Field(
        ...,
        description="1小时成交量归一化值",
        ge=-3.0,
        le=3.0
    )
    rsi_14_1h: int = Field(
        ...,
        description="1小时RSI(14)指标",
        ge=0,
        le=100
    )
    macd_line_1h: float = Field(
        ...,
        description="1小时MACD线"
    )
    macd_signal_1h: float = Field(
        ...,
        description="1小时MACD信号线"
    )
    macd_histogram_1h: float = Field(
        ...,
        description="1小时MACD柱状图"
    )
    
    # ==== 蜡烛图形态特征 (1H) ====
    upper_shadow_ratio_1h: float = Field(
        ...,
        description="1小时上影线比例",
        ge=0.0
    )
    lower_shadow_ratio_1h: float = Field(
        ...,
        description="1小时下影线比例",
        ge=0.0
    )
    shadow_imbalance_1h: float = Field(
        ...,
        description="1小时影线不平衡度",
        ge=-1.0,
        le=1.0
    )
    body_ratio_1h: float = Field(
        ...,
        description="1小时实体比例",
        ge=0.0,
        le=1.0
    )
    
    # ==== 15分钟周期指标 ====
    rsi_14_15m: int = Field(
        ...,
        description="15分钟RSI(14)指标",
        ge=0,
        le=100
    )
    volume_impulse_15m: float = Field(
        ...,
        description="15分钟成交量脉冲",
        ge=-1.0,
        le=1.0
    )
    macd_line_15m: float = Field(
        ...,
        description="15分钟MACD线"
    )
    macd_signal_15m: float = Field(
        ...,
        description="15分钟MACD信号线"
    )
    macd_histogram_15m: float = Field(
        ...,
        description="15分钟MACD柱状图"
    )
    atr_15m: float = Field(
        ...,
        description="15分钟ATR指标",
        ge=0.0
    )
    stoch_k_15m: int = Field(
        ...,
        description="15分钟随机指标K值",
        ge=0,
        le=100
    )
    stoch_d_15m: int = Field(
        ...,
        description="15分钟随机指标D值",
        ge=0,
        le=100
    )
    
    # ==== 4小时周期指标 ====
    rsi_14_4h: int = Field(
        ...,
        description="4小时RSI(14)指标",
        ge=0,
        le=100
    )
    trend_continuation_4h: int = Field(
        ...,
        description="4小时趋势延续信号",
        ge=0,
        le=1
    )
    macd_line_4h: float = Field(
        ...,
        description="4小时MACD线"
    )
    macd_signal_4h: float = Field(
        ...,
        description="4小时MACD信号线"
    )
    macd_histogram_4h: float = Field(
        ...,
        description="4小时MACD柱状图"
    )
    atr_4h: float = Field(
        ...,
        description="4小时ATR指标",
        ge=0.0
    )
    adx_4h: float = Field(
        ...,
        description="4小时ADX指标",
        ge=0.0
    )
    plus_di_4h: float = Field(
        ...,
        description="4小时+DI指标",
        ge=0.0
    )
    minus_di_4h: float = Field(
        ...,
        description="4小时-DI指标",
        ge=0.0
    )
    
    # ==== 4小时EMA指标 ====
    ema_12_4h: float = Field(
        ...,
        description="4小时12周期EMA"
    )
    ema_26_4h: float = Field(
        ...,
        description="4小时26周期EMA"
    )
    ema_48_4h: float = Field(
        ...,
        description="4小时48周期EMA"
    )
    ema_cross_4h_12_26: int = Field(
        ...,
        description="4小时EMA12/26金叉信号",
        ge=0,
        le=1
    )
    ema_cross_4h_26_48: int = Field(
        ...,
        description="4小时EMA26/48金叉信号",
        ge=0,
        le=1
    )
    
    # ==== 蜡烛图形态特征 (4H) ====
    upper_shadow_ratio_4h: float = Field(
        ...,
        description="4小时上影线比例",
        ge=0.0
    )
    lower_shadow_ratio_4h: float = Field(
        ...,
        description="4小时下影线比例",
        ge=0.0
    )
    shadow_imbalance_4h: float = Field(
        ...,
        description="4小时影线不平衡度",
        ge=-1.0,
        le=1.0
    )
    body_ratio_4h: float = Field(
        ...,
        description="4小时实体比例",
        ge=0.0,
        le=1.0
    )
    
    # ==== 日线周期指标 ====
    rsi_14_1d: int = Field(
        ...,
        description="日线RSI(14)指标",
        ge=0,
        le=100
    )
    atr_1d: float = Field(
        ...,
        description="日线ATR指标",
        ge=0.0
    )
    bollinger_upper_1d: float = Field(
        ...,
        description="日线布林带上轨"
    )
    bollinger_lower_1d: float = Field(
        ...,
        description="日线布林带下轨"
    )
    bollinger_position_1d: float = Field(
        ...,
        description="日线布林带位置(0-1之间)",
        ge=0.0,
        le=1.0
    )
    
    # ==== 蜡烛图形态特征 (1D) ====
    upper_shadow_ratio_1d: float = Field(
        ...,
        description="日线上影线比例",
        ge=0.0
    )
    lower_shadow_ratio_1d: float = Field(
        ...,
        description="日线下影线比例",
        ge=0.0
    )
    shadow_imbalance_1d: float = Field(
        ...,
        description="日线影线不平衡度",
        ge=-1.0,
        le=1.0
    )
    body_ratio_1d: float = Field(
        ...,
        description="日线实体比例",
        ge=0.0,
        le=1.0
    )
    
    # ==== 时间相关特征 ====
    hour_cos: float = Field(
        ...,
        description="小时余弦编码",
        ge=-1.0,
        le=1.0
    )
    hour_sin: float = Field(
        ...,
        description="小时正弦编码",
        ge=-1.0,
        le=1.0
    )
    day_of_week: int = Field(
        ...,
        description="星期几(0=周日, 1=周一, ..., 6=周六)",
        ge=0,
        le=6
    )
    
    # ==== 交易对信息 ====
    inst_id: str = Field(
        ...,
        description="交易对ID",
        pattern=r'^[A-Z]+-[A-Z]+(-[A-Z]+)?$',
        examples=['ETH-USDT-SWAP', 'BTC-USDT']
    )
    bar: TimeFrame = Field(
        ...,
        description="K线周期",
        examples=['1H', '15M', '4H', '1D']
    )
    
    # ===== 计算属性 =====
    @property
    def symbol(self) -> str:
        """提取交易对符号"""
        return self.inst_id.split('-')[0]
    
    @property
    def quote_currency(self) -> str:
        """提取报价货币"""
        parts = self.inst_id.split('-')
        return parts[1] if len(parts) > 1 else ''
    
    @property
    def instrument_type(self) -> InstrumentType:
        """提取交易对类型"""
        parts = self.inst_id.split('-')
        if len(parts) > 2:
            if parts[2] == 'SWAP':
                return InstrumentType.SWAP
            elif parts[2] == 'FUTURES':
                return InstrumentType.FUTURES
        return InstrumentType.SPOT
    
    @property
    def macd_divergence_1h(self) -> float:
        """计算1小时MACD背离程度"""
        return self.macd_line_1h - self.macd_signal_1h
    
    @property
    def macd_divergence_4h(self) -> float:
        """计算4小时MACD背离程度"""
        return self.macd_line_4h - self.macd_signal_4h
    
    @property
    def macd_divergence_15m(self) -> float:
        """计算15分钟MACD背离程度"""
        return self.macd_line_15m - self.macd_signal_15m
    
    @property
    def di_difference_4h(self) -> float:
        """计算4小时DI差值"""
        return self.plus_di_4h - self.minus_di_4h
    
    @property
    def is_rsi_oversold_1h(self) -> bool:
        """判断1小时RSI是否超卖"""
        return self.rsi_14_1h < 30
    
    @property
    def is_rsi_overbought_1h(self) -> bool:
        """判断1小时RSI是否超买"""
        return self.rsi_14_1h > 70
    
    @property
    def is_rsi_oversold_4h(self) -> bool:
        """判断4小时RSI是否超卖"""
        return self.rsi_14_4h < 30
    
    @property
    def is_rsi_overbought_4h(self) -> bool:
        """判断4小时RSI是否超买"""
        return self.rsi_14_4h > 70
    
    @property
    def is_bollinger_extreme_1d(self) -> bool:
        """判断日线布林带是否极端位置"""
        return self.bollinger_position_1d > 0.8 or self.bollinger_position_1d < 0.2
    
    # ===== 验证器 =====
    @field_validator('rsi_14_1h', 'rsi_14_15m', 'rsi_14_4h', 'rsi_14_1d')
    @classmethod
    def validate_rsi_range(cls, v: int) -> int:
        """验证RSI范围"""
        if not 0 <= v <= 100:
            raise ValueError(f'RSI值必须在0-100之间，当前值: {v}')
        return v
    
    @field_validator('stoch_k_15m', 'stoch_d_15m')
    @classmethod
    def validate_stoch_range(cls, v: int) -> int:
        """验证随机指标范围"""
        if not 0 <= v <= 100:
            raise ValueError(f'随机指标必须在0-100之间，当前值: {v}')
        return v
    
    @field_validator('shadow_imbalance_1h', 'shadow_imbalance_4h', 'shadow_imbalance_1d')
    @classmethod
    def validate_shadow_imbalance(cls, v: float) -> float:
        """验证影线不平衡度范围"""
        if not -1.0 <= v <= 1.0:
            raise ValueError(f'影线不平衡度必须在-1到1之间，当前值: {v}')
        return v
    
    @field_validator('body_ratio_1h', 'body_ratio_4h', 'body_ratio_1d')
    @classmethod
    def validate_body_ratio(cls, v: float) -> float:
        """验证实体比例范围"""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f'实体比例必须在0到1之间，当前值: {v}')
        return v
    
    @field_validator('bollinger_position_1d')
    @classmethod
    def validate_bollinger_position(cls, v: float) -> float:
        """验证布林带位置"""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f'布林带位置必须在0到1之间，当前值: {v}')
        return v
    
    class Config:
        """模型配置"""
        json_schema_extra = {
            "example": {
                "close_1h_normalized": 4.556,
                "volume_1h_normalized": -0.203,
                "rsi_14_1h": 30,
                "macd_line_1h": -1,
                "macd_signal_1h": 6,
                "macd_histogram_1h": -6.951,
                "hour_cos": -0.7071,
                "hour_sin": -0.7071,
                "day_of_week": 2,
                "upper_shadow_ratio_1h": 0.13,
                "lower_shadow_ratio_1h": 0.53,
                "shadow_imbalance_1h": -0.24,
                "body_ratio_1h": 0.6,
                "rsi_14_15m": 30,
                "volume_impulse_15m": 0.77,
                "macd_line_15m": -8,
                "macd_signal_15m": -6,
                "macd_histogram_15m": -1.705,
                "atr_15m": 8,
                "stoch_k_15m": 18,
                "stoch_d_15m": 21,
                "rsi_14_4h": 63,
                "trend_continuation_4h": 0,
                "macd_line_4h": 16,
                "macd_signal_4h": 11,
                "macd_histogram_4h": 5.048,
                "atr_4h": 45,
                "adx_4h": 17.3,
                "plus_di_4h": 18.4,
                "minus_di_4h": 11.9,
                "ema_12_4h": 4.588,
                "ema_26_4h": 4.561,
                "ema_48_4h": 4.544,
                "ema_cross_4h_12_26": 1,
                "ema_cross_4h_26_48": 1,
                "upper_shadow_ratio_4h": 2.43,
                "lower_shadow_ratio_4h": 0.74,
                "shadow_imbalance_4h": 0.41,
                "body_ratio_4h": 0.24,
                "rsi_14_1d": 50,
                "atr_1d": 122,
                "bollinger_upper_1d": 4.995,
                "bollinger_lower_1d": 3.99,
                "bollinger_position_1d": 0.56,
                "upper_shadow_ratio_1d": 0.14,
                "lower_shadow_ratio_1d": 0.09,
                "shadow_imbalance_1d": 0.04,
                "body_ratio_1d": 0.81,
                "inst_id": "ETH-USDT-SWAP",
                "bar": "1H"
            }
        }


# ===== 子模型定义 =====
class HourlyFeatures(BaseModel):
    """1小时周期特征"""
    close_normalized: float
    volume_normalized: float
    rsi: int
    macd_line: float
    macd_signal: float
    macd_histogram: float
    upper_shadow_ratio: float
    lower_shadow_ratio: float
    shadow_imbalance: float
    body_ratio: float


class FifteenMinuteFeatures(BaseModel):
    """15分钟周期特征"""
    rsi: int
    volume_impulse: float
    macd_line: float
    macd_signal: float
    macd_histogram: float
    atr: float
    stoch_k: int
    stoch_d: int


class FourHourFeatures(BaseModel):
    """4小时周期特征"""
    rsi: int
    trend_continuation: int
    macd_line: float
    macd_signal: float
    macd_histogram: float
    atr: float
    adx: float
    plus_di: float
    minus_di: float
    ema_12: float
    ema_26: float
    ema_48: float
    ema_cross_12_26: int
    ema_cross_26_48: int
    upper_shadow_ratio: float
    lower_shadow_ratio: float
    shadow_imbalance: float
    body_ratio: float


class DailyFeatures(BaseModel):
    """日线周期特征"""
    rsi: int
    atr: float
    bollinger_upper: float
    bollinger_lower: float
    bollinger_position: float
    upper_shadow_ratio: float
    lower_shadow_ratio: float
    shadow_imbalance: float
    body_ratio: float


class TimeFeatures(BaseModel):
    """时间特征"""
    hour_cos: float
    hour_sin: float
    day_of_week: int


class InstrumentInfo(BaseModel):
    """交易对信息"""
    inst_id: str
    bar: TimeFrame
    
# ===== 请求模型 =====

# ===== 响应模型 =====
class TechnicalIndicatorsResponse(BaseModel):
    """技术指标响应模型"""
    success: bool
    message: str
    data: TechnicalIndicatorsModel
    timestamp: int
    analysis: dict = None
    
    class Config:
        from_attributes = True