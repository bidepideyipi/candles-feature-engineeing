# Technical Analysis Helper

A Python project that uses XGBoost to predict cryptocurrency price movements based on technical indicators from OKX exchange.

🎉 **Happy Year of the Horse! Wishing you prosperity and success!** 🐴

## Features
- 📊 Fetches candlestick data from OKX API across multiple timeframes (15m, 1H, 4H, 1D)
- 📈 Calculates technical indicators (RSI, MACD, ATR, Stochastic, ADX, EMA) across multiple time windows
- 💾 Stores data in MongoDB for persistence
- 🤖 Trains XGBoost classification model for price movement prediction
- 🔮 Outputs classification with confidence scores
- 🎯 5-class classification system for price movement prediction (74.75% accuracy)

## Model Performance

### Version 1.0
- **Accuracy**: 74.75%
- **Cross-validation Accuracy**: 73.50% (±3.21%)
- **Features**: 40 technical indicators
- **Training Samples**: 13,338
- **Classes**: 5 (暴跌/下跌/横盘/上涨/暴涨)

### Classification System

| Class | Description | Price Range | Confidence | Training Samples |
|-------|-------------|-------------|------------|-----------------|
| 1 | 暴跌 (Heavy Down) | < -3.6% | 76.11% | 1,763 |
| 2 | 下跌 (Down) | -3.6% to -1.2% | 58.71% | 2,536 |
| 3 | 横盘 (Sideways) | -1.2% to 1.2% | 59.24% | 4,710 |
| 4 | 上涨 (Up) | 1.2% to 3.6% | 56.70% | 2,626 |
| 5 | 暴涨 (Heavy Up) | > 3.6% | 74.81% | 1,703 |

### Top 5 Features
| Rank | Feature | Description |
|------|---------|-------------|
| 1 | bollinger_position_1d | Daily Bollinger Band position (long-term trend context) |
| 2 | atr_1d | Daily ATR (long-term volatility) |
| 3 | ema_48_4h | 4-hour 48-period EMA (medium-term trend) |
| 4 | bollinger_upper_1d | Daily Bollinger Band upper (resistance level) |
| 5 | bollinger_lower_1d | Daily Bollinger Band lower (support level) |

## Deployment

### Docker Deployment（推荐）

Docker 是最推荐的部署方式，因为它提供了一致的环境和简化的配置。

#### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 2GB 可用内存
- 至少 5GB 可用磁盘空间

#### 快速开始

1. **准备模型文件**

将训练好的模型文件放到 `models/` 目录：

```bash
models/xgboost_model.json
models/xgboost_model_scaler.pkl
models/xgboost_model_features.json
```

2. **启动服务**

```bash
# 使用 Docker Compose 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f api

# 停止服务
docker-compose down

# 停止并删除数据卷（慎用）
docker-compose down -v
```

3. **验证服务**

```bash
# 检查容器状态
docker-compose ps

# 检查健康状态
curl http://localhost:8000/health

# 测试预测接口
curl http://localhost:8000/fetch/5-predict?inst_id=ETH-USDT-SWAP
```

4. **更新应用**

当代码更新后，重新构建并启动：

```bash
docker-compose up -d --build
```

#### 数据持久化

Docker Compose 配置了以下数据卷：

- `mongodb_data`: MongoDB 数据
- `redis_data`: Redis 数据

数据会保存在 Docker 卷中，即使容器重启也不会丢失。

#### 环境配置

创建 `.env` 文件（参考 `.env.example`）：

```env
# MongoDB Configuration
MONGODB_URI=mongodb://mongodb:27017
MONGODB_DATABASE=technical_analysis
MONGODB_CANDLESTICKS_COLLECTION=candlesticks
MONGODB_FEATURES_COLLECTION=features
MONGODB_NORMALIZER_COLLECTION=normalizer

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=1

# OKX API Configuration
OKEX_API_BASE_URL=https://www.okx.com
INST_ID=ETH-USDT-SWAP

# Model Configuration
MODEL_SAVE_PATH=models/xgboost_model.json

# Production Mode
PRODUCTION_MODE=true
```

#### 监控和日志

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs api
docker-compose logs mongodb
docker-compose logs redis

# 实时跟踪日志
docker-compose logs -f api

# 查看容器资源使用情况
docker stats
```

#### 扩展应用

如需扩展应用实例（例如增加 API 实例）：

```yaml
# 在 docker-compose.yml 中修改
services:
  api:
    deploy:
      replicas: 3
```

#### 备份和恢复

```bash
# 备份 MongoDB 数据
docker-compose exec mongodb mongodump --archive=/data/db/backup_$(date +%Y%m%d).archive

# 恢复 MongoDB 数据
docker-compose exec -T mongodb mongorestore --archive=/data/db/backup_20250208.archive

# 备份模型文件
docker cp technical-analysis-api:/app/models ./models_backup
```

#### 故障排除

1. **容器无法启动**

```bash
# 查看详细日志
docker-compose logs api

# 检查配置
docker-compose config

# 重新构建
docker-compose build --no-cache
docker-compose up -d
```

2. **MongoDB 连接失败**

```bash
# 检查 MongoDB 容器状态
docker-compose ps mongodb

# 查看 MongoDB 日志
docker-compose logs mongodb

# 进入 MongoDB 容器
docker-compose exec mongodb bash
```

3. **Redis 连接失败**

```bash
# 检查 Redis 容器状态
docker-compose ps redis

# 查看 Redis 日志
docker-compose logs redis

# 测试 Redis 连接
docker-compose exec redis redis-cli ping
```

4. **端口冲突**

如果默认端口被占用，修改 `docker-compose.yml` 中的端口映射：

```yaml
services:
  mongodb:
    ports:
      - "27018:27017"  # 使用 27018 端口
  
  redis:
    ports:
      - "6380:6379"   # 使用 6380 端口
  
  api:
    ports:
      - "8001:8000"   # 使用 8001 端口
```

### Traditional Deployment

## Prerequisites
- Python 3.8+
- MongoDB (local or remote)
- Virtual environment (recommended)

## Quick Start

### 1. Setup Environment
```bash
# Clone repository
git clone <repository-url>
cd technial_analysis_helper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Copy and edit configuration file
cp .env.example .env
```

Edit `.env` with your settings:
```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=technical_analysis
MONGODB_CANDLESTICKS_COLLECTION=candlesticks
MONGODB_FEATURES_COLLECTION=features
MONGODB_NORMALIZER_COLLECTION=normalizer

# Redis Configuration (for rate limiting)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1

# OKX API Configuration
OKEX_API_BASE_URL=https://www.okx.com

# Model Configuration
MODEL_SAVE_PATH=models/xgboost_model.json
FEATURE_WINDOW_SIZE=300
```

### 3. Start Services
Make sure MongoDB and Redis are running:
```bash
# Start MongoDB (if not already running)
mongod

# Start Redis (if not already running)
redis-server
```

### 4. Test System
```bash
# Test data collection and normalization
python -m pytest tests/collector/test_step_1_pull_quick.py -v
python -m pytest tests/collector/test_step_2_normalize.py -v

# Test feature generation
python -m pytest tests/collector/test_step_3_feature_merge.py -v
```

### 5. Data Pipeline (Step-by-Step)

#### Step 1: Pull Historical Data
```bash
# Quick pull (100 records per timeframe)
curl http://localhost:8000/fetch/pull-quick?inst_id=ETH-USDT-SWAP

# Or large pull
curl http://localhost:8000/fetch/1-pull-large?inst_id=ETH-USDT-SWAP&bar=1H&max_records=1000
```

#### Step 2: Normalize Data
```bash
curl http://localhost:8000/fetch/2-normalize?inst_id=ETH-USDT-SWAP&bar=1H
```

#### Step 3: Merge Features
```bash
curl http://localhost:8000/fetch/3-merge-feature?inst_id=ETH-USDT-SWAP&limit=3000
```

#### Step 4: Label Data
```bash
curl http://localhost:8000/fetch/4-lable?inst_id=ETH-USDT-SWAP
```

### 6. Train Model
Use Jupyter notebook for training:
```bash
jupyter notebook notebooks/model_training.ipynb
```

Or train programmatically:
```python
from src.models.xgboost_trainer import xgb_trainer

# Train 5-class model
results = xgb_trainer.train_model(
    inst_id='ETH-USDT-SWAP',
    bar='1H',
    limit=3000,
    test_size=0.2,
    cv_folds=5,
    use_class_weight=True
)
```

### 7. Make Predictions
```python
from src.models.xgboost_trainer import xgb_trainer

# Load trained model
xgb_trainer.load_model()

# Make prediction
predictions, probabilities = xgb_trainer.predict_single(feature_dict)

# Convert back to original labels (1-5)
predicted_class = predictions[0] + 1  # 0-indexed to 1-indexed
confidence = probabilities[predicted_class - 1]
```

## Usage Examples

### REST API Endpoints

#### Data Fetching
```bash
# Get history count
curl http://localhost:8000/fetch/history-count?inst_id=ETH-USDT-SWAP&bar=1H

# Quick pull
curl http://localhost:8000/fetch/pull-quick?inst_id=ETH-USDT-SWAP

# Large pull
curl http://localhost:8000/fetch/1-pull-large?inst_id=ETH-USDT-SWAP&bar=1H&max_records=60000

# Normalize data
curl http://localhost:8000/fetch/2-normalize?inst_id=ETH-USDT-SWAP&bar=1H

# Merge features
curl http://localhost:8000/fetch/3-merge-feature?inst_id=ETH-USDT-SWAP&limit=5000

# Label data
curl http://localhost:8000/fetch/4-lable?inst_id=ETH-USDT-SWAP
```

#### Prediction
```bash
# Get real-time prediction (5-class model)
curl http://localhost:8000/fetch/5-predict?inst_id=ETH-USDT-SWAP
```

Response example:
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

#### Production Mode
To disable data collection endpoints in production:
```env
PRODUCTION_MODE=true
```

When `PRODUCTION_MODE=true`, the following endpoints will return 403 Forbidden:
- `/fetch/history-count`
- `/fetch/pull-quick`
- `/fetch/1-pull-large`
- `/fetch/2-normalize`
- `/fetch/3-merge-feature`
- `/fetch/4-lable`

Only the prediction endpoint `/fetch/5-predict` will remain available.

### Programmatic Usage

#### Feature Generation
```python
from feature.feature_merge import FeatureMerge

# Merge features across all timeframes
feature_merge = FeatureMerge()
feature_merge.loop(limit=5000)
```

#### Technical Indicators
```python
from utils.rsi_calculator import RSI_CALCULATOR
from utils.macd_calculator import MACD_CALCULATOR
from utils.atr_calculator import ATR_CALCULATOR
from utils.stoch_calculator import STOCHASTIC_CALCULATOR
from utils.adx_calculator import ADX_CALCULATOR
from utils.ema_calculator import EMA_12, EMA_26

# Calculate indicators
rsi_value = RSI_CALCULATOR.calculate(close_prices)
macd_line, macd_signal, macd_hist = MACD_CALCULATOR.calculate(close_prices)
atr_value = ATR_CALCULATOR.calculate(df)
stoch_k, stoch_d = STOCHASTIC_CALCULATOR.calculate(df)
adx_value, plus_di, minus_di = ADX_CALCULATOR.calculate(df)
ema_12_value = EMA_12.calculate(close_prices)
```

## Project Structure
```
├── src/
│   ├── api/
│   │   └── api_fetch_okex.py        # OKX API endpoints
│   ├── collect/
│   │   ├── candlestick_handler.py    # MongoDB candlestick operations
│   │   ├── feature_handler.py        # MongoDB feature operations
│   │   ├── normalization_handler.py # MongoDB normalization params operations
│   │   └── okex_fetcher.py       # OKX API client
│   ├── config/
│   │   └── settings.py            # Configuration management
│   ├── feature/
│   │   ├── feature_1h_creator.py    # 1-hour feature creation
│   │   ├── feature_15m_creator.py   # 15-minute feature creation
│   │   ├── feature_4h_creator.py    # 4-hour feature creation
│   │   ├── feature_1D_creator.py    # 1-day feature creation
│   │   └── feature_merge.py         # Merge features across timeframes
│   ├── models/
│   │   └── xgboost_trainer.py     # XGBoost model training and prediction
│   └── utils/
│       ├── rsi_calculator.py       # RSI indicator
│       ├── macd_calculator.py      # MACD indicator
│       ├── atr_calculator.py       # ATR indicator
│       ├── stoch_calculator.py     # Stochastic oscillator
│       ├── adx_calculator.py      # ADX indicator
│       ├── ema_calculator.py       # EMA indicator
│       ├── trend_continuation_calculator.py  # Trend continuation strength
│       ├── normalize_encoder.py      # Data normalization
│       └── calculator_interface.py # Base interface for calculators
├── tests/
│   ├── calculator/                 # Unit tests for indicators
│   │   ├── test_rsi_calculator.py
│   │   ├── test_macd_calculator.py
│   │   ├── test_atr_calculator.py
│   │   ├── test_stoch_calculator.py
│   │   ├── test_adx_calculator.py
│   │   └── test_ema_calculator.py
│   └── collector/                 # Integration tests
│       ├── test_step_1_pull_quick.py
│       ├── test_step_2_normalize.py
│       └── test_step_3_feature_merge.py
├── notebooks/
│   └── model_training.ipynb        # Model training workflow
├── docs/
│   └── 特征结构.md               # Feature structure documentation
├── models/                        # Saved models directory
├── requirements.txt               # Python dependencies
├── .env.example                  # Configuration template
└── README.md                     # This file
```

## Technical Details

### Data Pipeline

#### Multi-Timeframe Data Collection
1. **15m (15-minute)**: Short-term signals (RSI, MACD, ATR, Stochastic)
2. **1H (1-hour)**: Base layer (Price, Volume, RSI, MACD, Time encoding)
3. **4H (4-hour)**: Medium-term confirmation (RSI, MACD, Trend Continuation, ATR, ADX, EMA)
4. **1D (1-day)**: Long-term context (RSI, ATR)

#### Feature Engineering (40 Features)
```
1-Hour Base Layer (7 features):
  - close_1h_normalized, volume_1h_normalized
  - rsi_14_1h, macd_line_1h, macd_signal_1h, macd_histogram_1h
  - hour_cos, hour_sin, day_of_week

15-Minute High-Frequency (7 features):
  - rsi_14_15m, volume_impulse_15m
  - macd_line_15m, macd_signal_15m, macd_histogram_15m
  - atr_15m, stoch_k_15m, stoch_d_15m

4-Hour Medium-Term (13 features):
  - rsi_14_4h, trend_continuation_4h
  - macd_line_4h, macd_signal_4h, macd_histogram_4h
  - atr_4h, adx_4h, plus_di_4h, minus_di_4h
  - ema_12_4h, ema_26_4h, ema_48_4h
  - ema_cross_4h_12_26, ema_cross_4h_26_48

1-Day Long-Term (5 features):
  - rsi_14_1d, atr_1d
  - bollinger_upper_1d, bollinger_lower_1d, bollinger_position_1d
```

#### Model Architecture
- **Algorithm**: XGBoost (Gradient Boosting)
- **Task**: Multi-class classification (3 classes)
- **Features**: 27 technical indicators across 4 timeframes
- **Validation**: 5-fold cross-validation with stratified sampling
- **Class Weights**: Balanced weights for handling class imbalance

### Technical Indicators

| Indicator | Timeframe | Window | Purpose |
|-----------|-----------|---------|---------|
| RSI | All | 14 | Momentum oscillator |
| MACD | All | (12, 26, 9) | Trend following |
| MACD Histogram | All | (12, 26, 9) | Momentum strength |
| ATR | All | 14 | Volatility measurement |
| Stochastic | 15m | (14, 3) | Overbought/Oversold |
| ADX | 4h | 14 | Trend strength |
| +DI/-DI | 4h | 14 | Trend direction |
| EMA | 4h | 12, 26, 48 | Exponential moving average |
| EMA Crossover | 4h | (12, 26), (26, 48) | Trend change signal |
| Trend Continuation | 4h | 48 | Trend strength metric |
| Bollinger Bands | 1d | (20, 2.0) | Price range & position |

## Configuration

### Classification Thresholds

Edit `src/config/settings.py` to adjust classification ranges:

```python
CLASSIFICATION_THRESHOLDS = {
    1: (-100, -3.6),     # 暴跌: < -3.6%
    2: (-3.6, -1.2),     # 下跌: -3.6% to -1.2%
    3: (-1.2, 1.2),      # 横盘: -1.2% to 1.2%
    4: (1.2, 3.6),       # 上涨: 1.2% to 3.6%
    5: (3.6, 100),       # 暴涨: > 3.6%
}
```

### Model Parameters
XGBoost parameters can be adjusted in `src/models/xgboost_trainer.py`:

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

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Ensure MongoDB is running: `mongod`
   - Check connection string in `.env`
   - Verify firewall settings

2. **API Errors**
   - Check internet connectivity
   - Verify OKX API is accessible
   - Check rate limits

3. **Import Errors**
   - Ensure virtual environment is activated
   - Reinstall dependencies: `pip install -r requirements.txt`

4. **Insufficient Data**
   - Increase `limit` during feature merge
   - Check OKX API response

### Debugging
```bash
# Enable logging in tests
python -m pytest tests/collector/test_step_3_feature_merge.py -v -s

# Check MongoDB data
python -c "from collect.candlestick_handler import candlestick_handler; print(candlestick_handler.count('ETH-USDT-SWAP', '1H'))"

# Test individual components
python -m pytest tests/calculator/test_adx_calculator.py -v
```

## Release Notes

### Version 1.0
- Initial release with multi-timeframe feature engineering
- 40 technical indicators across 4 timeframes (15m, 1H, 4H, 1D)
- 5-class classification system (74.75% accuracy)
- Support for: RSI, MACD, MACD Histogram, ATR, Stochastic, ADX, EMA, EMA Crossover, Trend Continuation, Bollinger Bands
- Comprehensive test coverage for all calculators
- RESTful API for data pipeline automation
- Real-time prediction endpoint with 5-class model support
- Unique indexes on features collection to prevent duplicate data (inst_id, timestamp, bar)
- Unique indexes on candlesticks collection to prevent duplicate data (inst_id, timestamp, bar)
- Unique indexes on normalizer collection to prevent duplicate data (inst_id, bar, column)
- Production mode to disable data collection endpoints (PRODUCTION_MODE=true)
- Automatic duplicate cleanup on index creation

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### MIT License

```
MIT License

Copyright (c) 2026 Technical Analysis Helper

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
