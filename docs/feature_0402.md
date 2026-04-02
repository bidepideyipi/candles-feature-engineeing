rsi_14_1d: 46,
atr_1d: 108,
bollinger_upper_1d: -0.272,
bollinger_lower_1d: -0.746,
bollinger_position_1d: 0.54,
upper_shadow_ratio_1d: 0.29,
lower_shadow_ratio_1d: 0.01,
shadow_imbalance_1d: 0.22,
body_ratio_1d: 0.77,
macd_line_1d: 16,
macd_signal_1d: 28,
rsi_14_4h: 74,
trend_continuation_4h: 0,
macd_line_4h: 4,
macd_signal_4h: -16,
macd_histogram_4h: 20.714,
atr_4h: 43,
adx_4h: 15.7,
plus_di_4h: 33.9,
minus_di_4h: 9.5,
ema_12_4h: -0.557,
ema_26_4h: -0.574,
ema_48_4h: -0.562,
ema_cross_4h_12_26: 1,
ema_cross_4h_26_48: -1,
upper_shadow_ratio_4h: 0.94,
lower_shadow_ratio_4h: 0.1,
shadow_imbalance_4h: 0.41,
body_ratio_4h: 0.49,
rsi_14_15m: 86,
volume_impulse_15m: 1.23,
macd_line_15m: 19,
macd_signal_15m: 11,
macd_histogram_15m: 8.128,
atr_15m: 11,
stoch_k_15m: 91,
stoch_d_15m: 96,
close_1h_normalized: -0.469,
volume_1h_normalized: 2.391,
rsi_14_1h: 71,
macd_line_1h: 30,
macd_signal_1h: 22,
macd_histogram_1h: 7.519,
hour_cos: -0.866,
hour_sin: -0.5,
day_of_week: 2,
upper_shadow_ratio_1h: 0.2,
lower_shadow_ratio_1h: 0,
shadow_imbalance_1h: 0.16,
body_ratio_1h: 0.84,
atr_1h: 24,
adx_1h: 56.2,
plus_di_1h: 31.9,
minus_di_1h: 9.3,
ema_12_1h: -0.519,
ema_26_1h: -0.54,
ema_48_1h: -0.554,
ema_cross_1h_12_26: 1,
ema_cross_1h_26_48: 1,
## 特征变更总结

### 1. feature_1d_creator.py 新增特征

| 特征名 | 说明 | 精度 |
|--------|------|------|
| `macd_line_1d` | MACD快线 | 0位小数 |
| `macd_signal_1d` | MACD信号线 | 0位小数 |

**变更详情**:
- 新增 `MACD_CALCULATOR` 导入
- 计算 MACD 指标 (12, 26, 9 参数)

---

### 2. feature_1h_creator.py 新增特征

| 特征名 | 说明 | 精度 |
|--------|------|------|
| `atr_1h` | 1小时波动率 | 0位小数 |
| `adx_1h` | 1小时趋势强度 | 1位小数 |
| `plus_di_1h` | 1小时上涨方向指标 | 1位小数 |
| `minus_di_1h` | 1小时下跌方向指标 | 1位小数 |
| `ema_12_1h` | 1小时12周期均线 (标准化) | 3位小数 |
| `ema_26_1h` | 1小时26周期均线 (标准化) | 3位小数 |
| `ema_48_1h` | 1小时48周期均线 (标准化) | 3位小数 |
| `ema_cross_1h_12_26` | EMA交叉信号 (12 vs 26) | - |
| `ema_cross_1h_26_48` | EMA交叉信号 (26 vs 48) | - |

**变更详情**:
- 新增导入: `ATR_CALCULATOR`, `ADX_CALCULATOR`, `EMA_12`, `EMA_26`, `EMA_48`, `EMACrossoverSignal`
- 新增 ATR 波动率指标
- 新增 ADX 趋势强度指标及方向指标 (+DI/-DI)
- 新增 3 条 EMA 均线及 2 个交叉信号

---

### 3. 特征数量变化

| 时间框架 | 原有 | 新增 | 现有 |
|---------|------|------|------|
| 1小时基础层 | 13 | **+9** | 22 |
| 1日线框架 | 9 | **+2** | 11 |

---

### 4. 新增计算器依赖

| 计算器 | 文件 | 用于 |
|--------|------|------|
| `ATR_CALCULATOR` | atr_calculator.py | 1H 波动率 |
| `ADX_CALCULATOR` | adx_calculator.py | 1H 趋势强度 |
| `EMA_12/26/48` | ema_calculator.py | 1H 均线系统 |
| `MACD_CALCULATOR` | macd_calculator.py | 1D 趋势跟踪 |