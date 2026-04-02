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