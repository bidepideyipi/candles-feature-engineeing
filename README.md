# Technical Analysis Helper

A Python project that uses XGBoost to predict cryptocurrency price movements based on technical indicators from OKX exchange.

## Features
- 📊 Fetches candlestick data from OKX API across multiple timeframes (15m, 1H, 4H, 1D)
- 📈 Calculates technical indicators (RSI, MACD, ATR, Stochastic, ADX, EMA) across multiple time windows
- 💾 Stores data in MongoDB for persistence
- 🤖 Trains XGBoost classification model for price movement prediction
- 🔮 Outputs classification with confidence scores
- 🎯 3-class classification system for price movement prediction (82%+ accuracy)

## Model Performance

### Version 1.0
- **Accuracy**: 82.18%
- **Cross-validation Accuracy**: 80.15% (±2.06%)
- **Features**: 27 technical indicators
- **Training Samples**: 12,119
- **Classes**: 3 (Down/Sideways/Up)

### Classification System
The model predicts price movements in following categories:

| Class | Description | Price Range | Confidence |
|-------|-------------|-------------|------------|
| 1 | Down | < -1.2% | 63.79% |
| 2 | Sideways | -1.2% to 1.2% | 54.31% |
| 3 | Up | > 1.2% | 64.89% |

### Top 5 Features
| Rank | Feature | Description |
|------|---------|-------------|
| 1 | day_of_week | Day of week (cyclical feature) |
| 2 | ema_48_4h | 4-hour 48-period EMA (medium-term trend) |
| 3 | rsi_1d | Daily RSI (long-term momentum) |
| 4 | atr_1d | Daily ATR (long-term volatility) |
| 5 | ema_26_4h | 4-hour 26-period EMA (medium-term trend) |

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
curl http://localhost:8000/fetch/3-merge-feature?inst_id=ETH-USDT-SWAP&limit=5000
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

# Train model
results = xgb_trainer.train_model(
    inst_id='ETH-USDT-SWAP',
    bar='1H',
    limit=15000,
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

# Convert back to original labels (1-3)
predicted_class = predictions[0]
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

#### Feature Engineering (27 Features)
```
1-Hour Base Layer (5 features):
  - close_1h_normalized, volume_1h_normalized
  - rsi_14_1h, macd_line_1h, macd_signal_1h

Time Encoding (3 features):
  - hour_cos, hour_sin, day_of_week

15-Minute High-Frequency (7 features):
  - rsi_14_15m, volume_impulse_15m
  - macd_line_15m, macd_signal_15m
  - atr_15m, stoch_k_15m, stoch_d_15m

4-Hour Medium-Term (10 features):
  - rsi_14_4h, trend_continuation_4h
  - macd_line_4h, macd_signal_4h
  - atr_4h, adx_4h, plus_di_4h, minus_di_4h
  - ema_12_4h, ema_26_4h, ema_48_4h

1-Day Long-Term (2 features):
  - rsi_14_1d, atr_1d
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
| ATR | All | 14 | Volatility measurement |
| Stochastic | 15m | (14, 3) | Overbought/Oversold |
| ADX | 4h | 14 | Trend strength |
| +DI/-DI | 4h | 14 | Trend direction |
| EMA | 4h | 12, 26, 48 | Exponential moving average |
| Trend Continuation | 4h | 48 | Trend strength metric |

## Configuration

### Classification Thresholds
Edit `src/config/settings.py` to adjust classification ranges:

```python
CLASSIFICATION_THRESHOLDS = {
    1: (-100, -1.2),    # Down: < -1.2%
    2: (-1.2, 1.2),     # Sideways: -1.2% to 1.2%
    3: (1.2, 100),       # Up: > 1.2%
}
```

### Model Parameters
XGBoost parameters can be adjusted in `src/models/xgboost_trainer.py`:

```python
params = {
    'objective': 'multi:softprob',
    'num_class': 3,
    'max_depth': 6,
    'learning_rate': 0.1,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'random_state': 42,
    'eval_metric': 'mlogloss'
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
- 27 technical indicators across 4 timeframes (15m, 1H, 4H, 1D)
- 3-class classification system (82% accuracy)
- Support for: RSI, MACD, ATR, Stochastic, ADX, EMA, Trend Continuation
- Comprehensive test coverage for all calculators
- RESTful API for data pipeline automation
- Unique indexes on features collection to prevent duplicate data (inst_id, timestamp, bar)
- Automatic duplicate cleanup on index creation

## License
MIT License - see LICENSE file for details.
