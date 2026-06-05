## 特征变更总结

### 优先级说明
- ⭐⭐⭐⭐⭐：核心优先级 - 多维度共通特征、关键转折点识别
- ⭐⭐⭐⭐：高优先级 - 重要补充特征
- ⭐⭐⭐：中优先级 - 辅助特征
- **[多维度共通]**：多个时间框架共同的特征，优先级最高

---

### 1. feature_4h_creator.py 新增特征

| 特征名 | 说明 | 精度 | 优先级 |
|--------|------|------|--------|
| `rsi_divergence_4h` | 4小时RSI背离信号 | - | ⭐⭐⭐⭐⭐ [多维度共通] |
| `rsi_momentum_4h` | RSI变化率 | 2位小数 | ⭐⭐⭐⭐ |
| `atr_ratio_4h_1h` | 4H/1H ATR比值 | 2位小数 | ⭐⭐⭐⭐⭐ [多维度共通] |
| `atr_momentum_4h` | ATR变化率 | 2位小数 | ⭐⭐⭐⭐ [多维度共通] |
| `atr_percentile_48h` | 48H ATR分位数 | 2位小数 | ⭐⭐⭐⭐ |
| `volatility_expansion_4h` | 波动率扩张信号 | int | ⭐⭐⭐⭐⭐ [多维度共通] |
| `volatility_contraction_4h` | 波动率收缩信号 | int | ⭐⭐⭐ [多维度共通] |
| `macd_divergence_4h` | MACD背离信号 | - | ⭐⭐⭐⭐ [多维度共通] |
| `macd_momentum_4h` | MACD快线变化率 | 2位小数 | ⭐⭐⭐⭐ [多维度共通] |
| `macd_histogram_momentum_4h` | MACD柱状图变化率 | 2位小数 | ⭐⭐⭐⭐ [多维度共通] |
| `macd_alignment_4h_1h` | 4H/1H MACD方向一致性 | int | ⭐⭐⭐⭐ |
| `macd_alignment_4h_1d` | 4H/1D MACD方向一致性 | int | ⭐⭐⭐ |
| `macd_golden_cross_strength_4h` | 金叉强度 | 2位小数 | ⭐⭐⭐⭐ |
| `macd_death_cross_strength_4h` | 死叉强度 | 2位小数 | ⭐⭐⭐⭐ |
| `adx_strength_4h` | ADX趋势强度分类 | int | ⭐⭐⭐⭐⭐ |
| `adx_di_spread_4h` | +DI和-DI差值 | 1位小数 | ⭐⭐⭐⭐ |
| `ema_alignment_bullish_4h` | 多头排列 | int | ⭐⭐⭐⭐ [多维度共通] |
| `ema_alignment_bearish_4h` | 空头排列 | int | ⭐⭐⭐⭐ [多维度共通] |
| `ema_12_slope_4h` | EMA12斜率 | 3位小数 | ⭐⭐⭐⭐ [多维度共通] |
| `ema_26_slope_4h` | EMA26斜率 | 3位小数 | ⭐⭐⭐⭐ [多维度共通] |
| `ema_48_slope_4h` | EMA48斜率 | 3位小数 | ⭐⭐⭐⭐ [多维度共通] |
| `price_to_ema12_distance_4h` | 价格距EMA12距离 | 2位小数 | ⭐⭐⭐⭐ [多维度共通] |
| `price_to_ema26_distance_4h` | 价格距EMA26距离 | 2位小数 | ⭐⭐⭐ [多维度共通] |
| `price_momentum_4h` | 价格变化率 | 2位小数 | ⭐⭐⭐⭐⭐ [多维度共通] |
| `price_acceleration_4h` | 价格加速度 | 3位小数 | ⭐⭐⭐⭐ [多维度共通] |
| `price_range_24h` | 24H价格区间 | 2位小数 | ⭐⭐⭐ |
| `price_range_percent_24h` | 24H价格区间百分比 | 2位小数 | ⭐⭐⭐⭐ [多维度共通] |
| `price_position_in_range_24h` | 价格在区间位置 | 2位小数 | ⭐⭐⭐⭐ [多维度共通] |
| `volatility_adjusted_return_4h` | 波动率调整收益 | 3位小数 | ⭐⭐⭐⭐ [多维度共通] |
| `drawdown_risk_24h` | 24H回撤风险 | 2位小数 | ⭐⭐⭐ |
| `market_regime_4h` | 市场状态 | int | ⭐⭐⭐⭐⭐ [多维度共通] |
| `trend_strength_signal_4h` | 趋势强度综合信号 | float | ⭐⭐⭐⭐⭐ |

**变更详情**:
- [多维度共通] RSI背离检测：4H/1H/15M三周期背离
- [多维度共通] 波动率比值：多周期ATR比值、分位数、扩张收缩
- [多维度共通] MACD增强：动量、背离、多周期一致性
- [多维度共通] EMA增强：排列、斜率、价格距离（4H/1H双周期）
- [多维度共通] 价格行为：动量、加速度、区间分析
- [多维度共通] 市场状态：趋势/震荡/反转分类（4H/1H双周期）

---

### 2. feature_1h_creator.py 新增特征

| 特征名 | 说明 | 精度 | 优先级 |
|--------|------|------|--------|
| `rsi_divergence_1h` | 1小时RSI背离信号 | - | ⭐⭐⭐⭐⭐ [多维度共通] |
| `rsi_momentum_1h` | RSI变化率 | 2位小数 | ⭐⭐⭐ |
| `atr_momentum_1h` | ATR变化率 | 2位小数 | ⭐⭐⭐⭐ [多维度共通] |
| `atr_percentile_168h` | 168H ATR分位数 | 2位小数 | ⭐⭐⭐⭐ |
| `volatility_expansion_1h` | 波动率扩张信号 | int | ⭐⭐⭐⭐⭐ [多维度共通] |
| `volatility_contraction_1h` | 波动率收缩信号 | int | ⭐⭐⭐⭐⭐ [多维度共通] |
| `pinbar_pattern_1h` | Pinbar形态识别 | int | ⭐⭐⭐⭐⭐ |
| `pinbar_direction_1h` | Pinbar方向 | int | ⭐⭐⭐⭐⭐ |
| `engulfing_pattern_1h` | 吞没形态 | int | ⭐⭐⭐⭐ |
| `body_to_range_ratio_1h` | 实体占区间比例 | 2位小数 | ⭐⭐⭐⭐ |
| `upper_shadow_to_body_ratio_1h` | 上引线与实体比例 | 2位小数 | ⭐⭐⭐⭐⭐ |
| `lower_shadow_to_body_ratio_1h` | 下引线与实体比例 | 2位小数 | ⭐⭐⭐⭐⭐ |
| `consecutive_green_candles_1h` | 连续阳线数 | int | ⭐⭐⭐⭐⭐ |
| `consecutive_red_candles_1h` | 连续阴线数 | int | ⭐⭐⭐⭐⭐ |
| `candle_body_color_sequence_1h` | K线颜色序列 | int | ⭐⭐⭐⭐ |
| `price_momentum_1h` | 价格变化率 | 2位小数 | ⭐⭐⭐⭐⭐ [多维度共通] |
| `price_acceleration_1h` | 价格加速度 | 3位小数 | ⭐⭐⭐⭐⭐ [多维度共通] |
| `price_volatility_24h` | 24H价格波动率 | 2位小数 | ⭐⭐⭐⭐ |
| `price_volatility_168h` | 168H价格波动率 | 2位小数 | ⭐⭐⭐ |
| `price_distance_from_mean_24h` | 价格距24H均值 | 2位小数 | ⭐⭐⭐⭐ [多维度共通] |
| `price_z_score_24h` | 价格Z-score | 2位小数 | ⭐⭐⭐⭐ [多维度共通] |
| `volume_momentum_1h` | 成交量变化率 | 2位小数 | ⭐⭐⭐⭐ [多维度共通] |
| `volume_spike_1h` | 成交量异常放大 | int | ⭐⭐⭐⭐ |
| `volume_dry_up_1h` | 成交量异常萎缩 | int | ⭐⭐⭐⭐ |
| `volume_price_divergence_1h` | 量价背离 | int | ⭐⭐⭐⭐ |
| `obv_momentum_1h` | OBV动量 | 2位小数 | ⭐⭐⭐⭐ |
| `vwap_distance_1h` | 价格距VWAP距离 | 2位小数 | ⭐⭐⭐ |
| `volume_accumulation_24h` | 24H成交量净流入 | 2位小数 | ⭐⭐⭐⭐ |
| `asia_session_active` | 亚洲时段 | int | ⭐⭐⭐ |
| `europe_session_active` | 欧洲时段 | int | ⭐⭐⭐ |
| `us_session_active` | 美国时段 | int | ⭐⭐⭐ |
| `market_regime_1h` | 市场状态 | int | ⭐⭐⭐⭐⭐ [多维度共通] |
| `reversal_signal_1h` | 反转信号 | float | ⭐⭐⭐⭐ |
| `breakout_signal_1h` | 突破信号 | float | ⭐⭐⭐⭐ |
| `liquidity_score_1h` | 流动性评分 | 2位小数 | ⭐⭐⭐ |

**变更详情**:
- [多维度共通] RSI背离检测：与4H/15M形成三周期背离检测
- [多维度共通] 波动率扩张/收缩：与4H双周期确认
- [多维度共通] 价格行为：动量、加速度、Z-score（4H/1H双周期）
- [多维度共通] 市场状态：与4H双周期确认
- [多维度共通] 成交量动量：与15M双周期确认
- K线形态增强：Pinbar、吞没、连续K线分析（1H周期核心）
- 引线形态深度分析：与实体的比例关系

---

### 3. feature_15m_creator.py 新增特征

| 特征名 | 说明 | 精度 | 优先级 |
|--------|------|------|--------|
| `rsi_momentum_15m` | RSI变化率 | 2位小数 | ⭐⭐⭐ |
| `atr_momentum_15m` | ATR变化率 | 2位小数 | ⭐⭐⭐ |
| `macd_momentum_15m` | MACD快线变化率 | 2位小数 | ⭐⭐⭐ |
| `volume_momentum_15m` | 成交量变化率 | 2位小数 | ⭐⭐⭐⭐ [多维度共通] |
| `price_momentum_15m` | 价格变化率 | 2位小数 | ⭐⭐⭐⭐ [多维度共通] |
| `price_acceleration_15m` | 价格加速度 | 3位小数 | ⭐⭐⭐⭐ [多维度共通] |

**变更详情**:
- [多维度共通] 高频动量特征：与4H/1H形成多周期动量确认
- 捕捉短期价格变化：补充高频信号

---

### 4. feature_1d_creator.py 新增特征

| 特征名 | 说明 | 精度 | 优先级 |
|--------|------|------|--------|
| `bollinger_squeeze_1d` | 布林带压缩 | int | ⭐⭐⭐⭐⭐ |
| `bollinger_expansion_1d` | 布林带扩张 | int | ⭐⭐⭐⭐ |
| `bollinger_bandwidth_1d` | 布林带带宽 | 2位小数 | ⭐⭐⭐⭐ |
| `bollinger_momentum_1d` | 布林带位置变化率 | 2位小数 | ⭐⭐⭐ |
| `bollinger_alignment_1d_4h` | 1D/4H布林带一致性 | int | ⭐⭐⭐⭐ |
| `bollinger_alignment_1d_1h` | 1D/1H布林带一致性 | int | ⭐⭐⭐ |
| `market_sentiment_1d` | 市场情绪指标 | float | ⭐⭐⭐⭐ |

**变更详情**:
- 布林带增强：压缩/扩张/带宽/动量（1D周期关键指标）
- 多周期一致性：与4H/1H布林带对齐
- 市场情绪：长期情绪指标

---

### 5. 特征数量变化

| 时间框架 | 原有 | 新增 | 现有 | 变化率 |
|---------|------|------|------|--------|
| 1小时基础层 | 22 | **+38** | 60 | +173% |
| 4小时中期层 | 29 | **+31** | 62 | +107% |
| 15分钟高频层 | 6 | **+6** | 12 | +100% |
| 1日线长期层 | 11 | **+7** | 18 | +64% |
| **总计** | **68** | **+82** | **152** | **+121%** |

---

### 6. 新增计算器依赖

| 计算器 | 文件 | 用于 | 优先级 |
|--------|------|------|--------|
| `RSIDivergenceDetector` | rsi_divergence_calculator.py | RSI背离检测 | ⭐⭐⭐⭐⭐ |
| `MomentumCalculator` | momentum_calculator.py | 动量计算 | ⭐⭐⭐⭐⭐ |
| `VolatilityRatioCalculator` | volatility_ratio_calculator.py | 波动率比值 | ⭐⭐⭐⭐⭐ |
| `PercentileCalculator` | percentile_calculator.py | 分位数计算 | ⭐⭐⭐⭐ |
| `VolatilityDetector` | volatility_detector.py | 波动率扩张/收缩 | ⭐⭐⭐⭐⭐ |
| `MACDEnhancedCalculator` | macd_enhanced_calculator.py | MACD增强计算 | ⭐⭐⭐⭐ |
| `MACDDivergenceDetector` | macd_divergence_calculator.py | MACD背离检测 | ⭐⭐⭐⭐ |
| `EMASlopeCalculator` | ema_slope_calculator.py | EMA斜率 | ⭐⭐⭐⭐ |
| `PriceBehaviorCalculator` | price_behavior_calculator.py | 价格行为 | ⭐⭐⭐⭐⭐ |
| `CandlePatternDetector` | candle_pattern_calculator.py | K线形态 | ⭐⭐⭐⭐⭐ |
| `VolumeAnalysisCalculator` | volume_analysis_calculator.py | 成交量分析 | ⭐⭐⭐⭐ |
| `TimeSessionCalculator` | time_session_calculator.py | 时间周期 | ⭐⭐⭐ |
| `MarketRegimeClassifier` | market_regime_classifier.py | 市场状态 | ⭐⭐⭐⭐⭐ |
| `CompositeSignalGenerator` | composite_signal_calculator.py | 综合信号 | ⭐⭐⭐⭐⭐ |
| `BollingerEnhancedCalculator` | bollinger_enhanced_calculator.py | 布林带增强 | ⭐⭐⭐⭐ |

---

### 7. 多维度共通特征汇总

**核心多维度特征（优先级⭐⭐⭐⭐⭐）**

| 特征类别 | 涉及时间框架 | 特征数量 | 用途 |
|---------|-------------|---------|------|
| RSI背离 | 4H/1H | 2 | 关键转折点识别 |
| 波动率比值 | 4H/1H | 1 | 多周期波动率对比 |
| 波动率扩张/收缩 | 4H/1H | 4 | 波动率状态变化 |
| 价格动量/加速度 | 4H/1H/15M | 6 | 趋势强度确认 |
| 市场状态 | 4H/1H | 2 | 市场环境分类 |
| EMA排列/斜率 | 4H | 5 | 趋势方向确认 |
| 综合信号 | 4H | 1 | 多指标融合 |

**多维度特征统计：22个核心特征覆盖3-4个时间框架**

---

### 8. 实施优先级

#### 第一批（多维度共通特征，⭐⭐⭐⭐⭐）
预计提升：+3-5% 准确率

| 模块 | 新增特征数 | 预计开发时间 |
|------|-----------|-------------|
| RSI背离检测（4H/1H） | 2 | 2天 |
| 波动率比值/分位数 | 4 | 3天 |
| 波动率扩张/收缩（4H/1H） | 4 | 2天 |
| 价格动量/加速度（4H/1H/15M） | 6 | 3天 |
| 市场状态分类（4H/1H） | 2 | 3天 |
| EMA排列/斜率 | 5 | 2天 |
| 综合信号 | 1 | 1天 |
| **小计** | **24** | **16天** |

#### 第二批（高优先级特征，⭐⭐⭐⭐）
预计提升：+2-3% 准确率

| 模块 | 新增特征数 | 预计开发时间 |
|------|-----------|-------------|
| K线形态（Pinbar、吞没） | 5 | 3天 |
| MACD动量/背离 | 5 | 3天 |
| 成交量分析 | 6 | 3天 |
| 布林带增强 | 4 | 2天 |
| 价格区间分析 | 3 | 2天 |
| **小计** | **23** | **13天** |

#### 第三批（中优先级特征，⭐⭐⭐）
预计提升：+1-2% 准确率

| 模块 | 新增特征数 | 预计开发时间 |
|------|-----------|-------------|
| 其他补充特征 | 35 | 14天 |
| **小计** | **35** | **14天** |