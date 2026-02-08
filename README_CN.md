# 技术分析助手

一个使用 XGBoost 基于 OKX 交易所技术指标预测加密货币价格走势的 Python 项目。

## 功能特性
- 📊 从 OKX API 获取多时间周期的 K 线数据（15m, 1H, 4H, 1D）
- 📈 跨多个时间窗口计算技术指标（RSI, MACD, ATR, 随机震荡指标, ADX, EMA）
- 💾 使用 MongoDB 持久化存储数据
- 🤖 训练 XGBoost 分类模型进行价格走势预测
- 🔮 输出分类结果及置信度
- 🎯 5 类价格走势预测分类系统（准确率 74.75%）

## 模型性能

### 版本 1.0
- **准确率**: 74.75%
- **交叉验证准确率**: 73.50% (±3.21%)
- **特征数量**: 40 个技术指标
- **训练样本**: 13,338 条
- **分类类别**: 5 类（暴跌/下跌/横盘/上涨/暴涨）

### 分类系统

| 类别 | 描述 | 价格区间 | 置信度 | 训练样本数 |
|------|------|---------|--------|-----------|
| 1 | 暴跌 | < -3.6% | 76.11% | 1,763 |
| 2 | 下跌 | -3.6% ~ -1.2% | 58.71% | 2,536 |
| 3 | 横盘 | -1.2% ~ 1.2% | 59.24% | 4,710 |
| 4 | 上涨 | 1.2% ~ 3.6% | 56.70% | 2,626 |
| 5 | 暴涨 | > 3.6% | 74.81% | 1,703 |

### Top 5 特征
| 排名 | 特征 | 描述 |
|------|------|------|
| 1 | bollinger_position_1d | 日线布林带位置（长期趋势背景） |
| 2 | atr_1d | 日线 ATR（长期波动率） |
| 3 | ema_48_4h | 4小时 48期 EMA（中期趋势） |
| 4 | bollinger_upper_1d | 日线布林带上轨（阻力位） |
| 5 | bollinger_lower_1d | 日线布林带下轨（支撑位） |

## 前置要求
- Python 3.8+
- MongoDB（本地或远程）
- 虚拟环境（推荐）

## 快速开始

### 1. 环境搭建
```bash
# 克隆仓库
git clone <repository-url>
cd technial_analysis_helper

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置
```bash
# 复制并编辑配置文件
cp .env.example .env
```

编辑 `.env` 文件，设置您的配置：
```env
# MongoDB 配置
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=technical_analysis
MONGODB_CANDLESTICKS_COLLECTION=candlesticks
MONGODB_FEATURES_COLLECTION=features
MONGODB_NORMALIZER_COLLECTION=normalizer

# Redis 配置（用于限流）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1

# OKX API 配置
OKEX_API_BASE_URL=https://www.okx.com

# 模型配置
MODEL_SAVE_PATH=models/xgboost_model.json
FEATURE_WINDOW_SIZE=300
```

### 3. 启动服务
确保 MongoDB 和 Redis 正在运行：
```bash
# 启动 MongoDB（如果未运行）
mongod

# 启动 Redis（如果未运行）
redis-server
```

### 4. 测试系统
```bash
# 测试数据采集和归一化
python -m pytest tests/collector/test_step_1_pull_quick.py -v
python -m pytest tests/collector/test_step_2_normalize.py -v

# 测试特征生成
python -m pytest tests/collector/test_step_3_feature_merge.py -v
```

### 5. 数据流水线（分步执行）

#### 步骤 1：拉取历史数据
```bash
# 快速拉取（每个周期 100 条记录）
curl http://localhost:8000/fetch/pull-quick?inst_id=ETH-USDT-SWAP

# 或大规模拉取
curl http://localhost:8000/fetch/1-pull-large?inst_id=ETH-USDT-SWAP&bar=1H&max_records=1000
```

#### 步骤 2：归一化数据
```bash
curl http://localhost:8000/fetch/2-normalize?inst_id=ETH-USDT-SWAP&bar=1H
```

#### 步骤 3：合并特征
```bash
curl http://localhost:8000/fetch/3-merge-feature?inst_id=ETH-USDT-SWAP&limit=3000
```

#### 步骤 4：标注数据
```bash
curl http://localhost:8000/fetch/4-lable?inst_id=ETH-USDT-SWAP
```

### 6. 训练模型
使用 Jupyter notebook 进行训练：
```bash
jupyter notebook notebooks/model_training.ipynb
```

或通过代码训练：
```python
from src.models.xgboost_trainer import xgb_trainer

# 训练 5 类模型
results = xgb_trainer.train_model(
    inst_id='ETH-USDT-SWAP',
    bar='1H',
    limit=3000,
    test_size=0.2,
    cv_folds=5,
    use_class_weight=True
)
```

### 7. 进行预测
```python
from src.models.xgboost_trainer import xgb_trainer

# 加载训练好的模型
xgb_trainer.load_model()

# 进行预测
predictions, probabilities = xgb_trainer.predict_single(feature_dict)

# 转换为原始标签（1-5）
predicted_class = predictions[0] + 1  # 从 0 索引转换为 1 索引
confidence = probabilities[predicted_class - 1]
```

## 使用示例

### REST API 接口

#### 数据采集
```bash
# 获取历史数据数量
curl http://localhost:8000/fetch/history-count?inst_id=ETH-USDT-SWAP&bar=1H

# 快速拉取
curl http://localhost:8000/fetch/pull-quick?inst_id=ETH-USDT-SWAP

# 大规模拉取
curl http://localhost:8000/fetch/1-pull-large?inst_id=ETH-USDT-SWAP&bar=1H&max_records=60000

# 归一化数据
curl http://localhost:8000/fetch/2-normalize?inst_id=ETH-USDT-SWAP&bar=1H

# 合并特征
curl http://localhost:8000/fetch/3-merge-feature?inst_id=ETH-USDT-SWAP&limit=5000

# 标注数据
curl http://localhost:8000/fetch/4-lable?inst_id=ETH-USDT-SWAP
```

#### 预测
```bash
# 获取实时预测（5 类模型）
curl http://localhost:8000/fetch/5-predict?inst_id=ETH-USDT-SWAP
```

响应示例：
```json
{
  "timestamp": 1738780800000,
  "prediction": 3,
  "prediction_label": "横盘 (-1.2% ~ 1.2%)",
  "probabilities": {
    "1": 0.10,
    "2": 0.05,
    "3": 0.70,
    "4": 0.10,
    "5": 0.05
  }
}
```

#### 生产模式
在生产环境中禁用数据采集接口：
```env
PRODUCTION_MODE=true
```

当 `PRODUCTION_MODE=true` 时，以下接口将返回 403 Forbidden：
- `/fetch/history-count`
- `/fetch/pull-quick`
- `/fetch/1-pull-large`
- `/fetch/2-normalize`
- `/fetch/3-merge-feature`
- `/fetch/4-lable`

仅预测接口 `/fetch/5-predict` 保持可用。

### 编程使用

#### 特征生成
```python
from feature.feature_merge import FeatureMerge

# 合并所有时间周期的特征
feature_merge = FeatureMerge()
feature_merge.loop(limit=5000)
```

#### 技术指标
```python
from utils.rsi_calculator import RSI_CALCULATOR
from utils.macd_calculator import MACD_CALCULATOR
from utils.atr_calculator import ATR_CALCULATOR
from utils.stoch_calculator import STOCHASTIC_CALCULATOR
from utils.adx_calculator import ADX_CALCULATOR
from utils.ema_calculator import EMA_12, EMA_26

# 计算指标
rsi_value = RSI_CALCULATOR.calculate(close_prices)
macd_line, macd_signal, macd_hist = MACD_CALCULATOR.calculate(close_prices)
atr_value = ATR_CALCULATOR.calculate(df)
stoch_k, stoch_d = STOCHASTIC_CALCULATOR.calculate(df)
adx_value, plus_di, minus_di = ADX_CALCULATOR.calculate(df)
ema_12_value = EMA_12.calculate(close_prices)
```

## 项目结构
```
├── src/
│   ├── api/
│   │   └── api_fetch_okex.py        # OKX API 接口
│   ├── collect/
│   │   ├── candlestick_handler.py    # MongoDB K 线操作
│   │   ├── feature_handler.py        # MongoDB 特征操作
│   │   ├── normalization_handler.py # MongoDB 归一化参数操作
│   │   └── okex_fetcher.py       # OKX API 客户端
│   ├── config/
│   │   └── settings.py            # 配置管理
│   ├── feature/
│   │   ├── feature_1h_creator.py    # 1小时特征创建
│   │   ├── feature_15m_creator.py   # 15分钟特征创建
│   │   ├── feature_4h_creator.py    # 4小时特征创建
│   │   ├── feature_1D_creator.py    # 1天特征创建
│   │   └── feature_merge.py         # 合并多时间周期特征
│   ├── models/
│   │   └── xgboost_trainer.py     # XGBoost 模型训练和预测
│   └── utils/
│       ├── rsi_calculator.py       # RSI 指标
│       ├── macd_calculator.py      # MACD 指标
│       ├── atr_calculator.py       # ATR 指标
│       ├── stoch_calculator.py     # 随机震荡指标
│       ├── adx_calculator.py      # ADX 指标
│       ├── ema_calculator.py       # EMA 指标
│       ├── trend_continuation_calculator.py  # 趋势延续强度
│       ├── normalize_encoder.py      # 数据归一化
│       └── calculator_interface.py # 指标计算器基类接口
├── tests/
│   ├── calculator/                 # 指标单元测试
│   │   ├── test_rsi_calculator.py
│   │   ├── test_macd_calculator.py
│   │   ├── test_atr_calculator.py
│   │   ├── test_stoch_calculator.py
│   │   ├── test_adx_calculator.py
│   │   └── test_ema_calculator.py
│   └── collector/                 # 集成测试
│       ├── test_step_1_pull_quick.py
│       ├── test_step_2_normalize.py
│       └── test_step_3_feature_merge.py
├── notebooks/
│   └── model_training.ipynb        # 模型训练工作流
├── docs/
│   └── 特征结构.md               # 特征结构文档
├── models/                        # 保存模型的目录
├── requirements.txt               # Python 依赖
├── .env.example                  # 配置模板
└── README.md                     # 英文说明文档
```

## 技术细节

### 数据流水线

#### 多时间周期数据采集
1. **15m (15分钟)**: 短期信号（RSI, MACD, ATR, 随机震荡指标）
2. **1H (1小时)**: 基础层（价格、成交量、RSI、MACD、时间编码）
3. **4H (4小时)**: 中期确认（RSI, MACD, 趋势延续、ATR, ADX, EMA）
4. **1D (1天)**: 长期背景（RSI, ATR）

#### 特征工程（40 个特征）
```
1 小时基础层（7 个特征）:
  - close_1h_normalized, volume_1h_normalized
  - rsi_14_1h, macd_line_1h, macd_signal_1h, macd_histogram_1h
  - hour_cos, hour_sin, day_of_week

15 分钟高频层（7 个特征）:
  - rsi_14_15m, volume_impulse_15m
  - macd_line_15m, macd_signal_15m, macd_histogram_15m
  - atr_15m, stoch_k_15m, stoch_d_15m

4 小时中期层（13 个特征）:
  - rsi_14_4h, trend_continuation_4h
  - macd_line_4h, macd_signal_4h, macd_histogram_4h
  - atr_4h, adx_4h, plus_di_4h, minus_di_4h
  - ema_12_4h, ema_26_4h, ema_48_4h
  - ema_cross_4h_12_26, ema_cross_4h_26_48

1 天长期层（5 个特征）:
  - rsi_14_1d, atr_1d
  - bollinger_upper_1d, bollinger_lower_1d, bollinger_position_1d
```

#### 模型架构
- **算法**: XGBoost（梯度提升）
- **任务**: 多分类（5 个类别）
- **特征**: 40 个跨 4 个时间周期的技术指标
- **验证**: 5 折交叉验证，分层采样
- **类别权重**: 平衡权重处理类别不平衡

### 技术指标

| 指标 | 时间周期 | 窗口 | 用途 |
|-----------|-----------|---------|---------|
| RSI | 全部 | 14 | 动量震荡指标 |
| MACD | 全部 | (12, 26, 9) | 趋势跟踪 |
| MACD 柱状图 | 全部 | (12, 26, 9) | 动量强度 |
| ATR | 全部 | 14 | 波动率测量 |
| 随机震荡指标 | 15m | (14, 3) | 超买/超卖 |
| ADX | 4h | 14 | 趋势强度 |
| +DI/-DI | 4h | 14 | 趋势方向 |
| EMA | 4h | 12, 26, 48 | 指数移动平均 |
| EMA 交叉 | 4h | (12, 26), (26, 48) | 趋势变化信号 |
| 趋势延续 | 4h | 48 | 趋势强度指标 |
| 布林带 | 1d | (20, 2.0) | 价格区间和位置 |

## 配置

### 分类阈值

编辑 `src/config/settings.py` 调整分类区间：

```python
CLASSIFICATION_THRESHOLDS = {
    1: (-100, -3.6),     # 暴跌: < -3.6%
    2: (-3.6, -1.2),     # 下跌: -3.6% ~ -1.2%
    3: (-1.2, 1.2),      # 横盘: -1.2% ~ 1.2%
    4: (1.2, 3.6),       # 上涨: 1.2% ~ 3.6%
    5: (3.6, 100),       # 暴涨: > 3.6%
}
```

### 模型参数
XGBoost 参数可在 `src/models/xgboost_trainer.py` 中调整：

```python
params = {
    'objective': 'multi:softprob',
    'num_class': 5,
    'max_depth': 8,
    'learning_rate': 0.05,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'random_state': 42,
    'eval_metric': 'mlogloss',
    'min_child_weight': 3,
    'gamma': 0.1,
    'reg_alpha': 0.1,
    'reg_lambda': 1
}
```

## 故障排除

### 常见问题

1. **MongoDB 连接失败**
   - 确保 MongoDB 正在运行: `mongod`
   - 检查 `.env` 中的连接字符串
   - 验证防火墙设置

2. **API 错误**
   - 检查网络连接
   - 验证 OKX API 可访问性
   - 检查限流设置

3. **导入错误**
   - 确保虚拟环境已激活
   - 重新安装依赖: `pip install -r requirements.txt`

4. **数据不足**
   - 在特征合并时增加 `limit` 参数
   - 检查 OKX API 响应

### 调试
```bash
# 在测试中启用日志
python -m pytest tests/collector/test_step_3_feature_merge.py -v -s

# 检查 MongoDB 数据
python -c "from collect.candlestick_handler import candlestick_handler; print(candlestick_handler.count('ETH-USDT-SWAP', '1H'))"

# 测试单个组件
python -m pytest tests/calculator/test_adx_calculator.py -v
```

## 发布说明

### 版本 1.0
- 初始版本，包含多时间周期特征工程
- 跨 4 个时间周期的 40 个技术指标（15m, 1H, 4H, 1D）
- 5 类分类系统（准确率 74.75%）
- 支持：RSI, MACD, MACD 柱状图, ATR, 随机震荡指标, ADX, EMA, EMA 交叉, 趋势延续, 布林带
- 所有指标计算器的完整测试覆盖
- 用于数据流水线自动化的 RESTful API
- 支持 5 类模型的实时预测接口
- 特征集合的唯一索引防止重复数据（inst_id, timestamp, bar）
- K 线集合的唯一索引防止重复数据（inst_id, timestamp, bar）
- 归一化集合的唯一索引防止重复数据（inst_id, bar, column）
- 生产模式禁用数据采集接口（PRODUCTION_MODE=true）
- 索引创建时自动清理重复数据

## 许可证
MIT License - 详见 LICENSE 文件
