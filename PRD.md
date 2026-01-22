# PRD: ETH Options Hunter Tool

## Product Overview
A professional ETH options trading analysis tool that automates data collection, feature engineering, and machine learning model training for predicting ETH price movements. The system provides quantitative signals for options trading decisions.

## Core Architecture
The system consists of four modular components with independent entry points:
1. **Data Collector**: OKEx API integration with rate limiting
2. **Data Storage**: MongoDB persistence layer
3. **Feature Engine**: Technical indicator calculation and labeling
4. **ML Trainer**: Model training and evaluation

## 1. Data Collection Module

### API Integration
- **Exchange**: OKEx
- **Trading Pair**: ETH-USDT
- **Timeframe**: 1-hour candles
- **Batch Size**: 100 records per request
- **Traversal Direction**: Newest to oldest

### Rate Limiting
- **Constraint**: 20 requests per second
- **Implementation**: Token bucket algorithm
- **Buffer**: 50ms delay between requests

### Data Fields Collected
```python
{
    "timestamp": int,      # Unix timestamp
    "open": float,         # Opening price
    "high": float,         # Highest price
    "low": float,          # Lowest price
    "close": float,        # Closing price
    "volume": float,       # Trading volume
    "quote_volume": float  # Quote currency volume
}
```

### Error Handling
- Retry mechanism with exponential backoff
- Data validation and integrity checks
- Graceful degradation for partial failures

## 2. Data Storage Module

### Database Schema
```javascript
// Candlestick Collection
{
    "symbol": "ETH-USDT",
    "timestamp": ISODate,
    "open": Number,
    "high": Number,
    "low": Number,
    "close": Number,
    "volume": Number,
    "quote_volume": Number,
    "source": "okex"
}

// Feature Collection
{
    "timestamp": ISODate,
    "features": {
        "rsi_short": Number,
        "rsi_medium": Number,
        "rsi_long": Number,
        "bb_position_short": Number,
        "bb_position_medium": Number,
        "bb_position_long": Number,
        // ... other technical indicators
    },
    "label": Int,           // 1-7 classification
    "future_return": Number // Actual return for validation
}
```

### Indexing Strategy
- Compound index on `[symbol, timestamp]`
- TTL index for automatic cleanup (optional)
- Unique constraint on timestamp

## 3. Feature Engineering Module

### Time Windows
| Parameter | Periods | Duration |
|-----------|---------|----------|
| Short Term | 12 | 12 hours |
| Medium Term | 48 | 2 days |
| Long Term | 192 | 8 days |

### Technical Indicators
All technical indicators primarily use the common Time Windows configuration defined above, with special exceptions noted.

#### RSI (Relative Strength Index)
- **Calculation**: Standard RSI formula
- **Application**: Applied to all three timeframes (short, medium, long)
- **Output**: Three RSI values per sample

#### Bollinger Bands
- **Middle Band**: Simple Moving Average
- **Upper/Lower Bands**: SMA ± (2.5 × Standard Deviation)
- **Position Metric**: Normalized price position (0-1 scale)
- **Application**: Applied to all three timeframes (short, medium, long)
- **Rationale**: Increased standard deviation multiplier (2.5 vs 2.0) to accommodate ETH's high volatility characteristics

#### MACD (Moving Average Convergence Divergence)
- **Fast Line**: 12-period EMA (using Short Term time window)
- **Slow Line**: 48-period EMA (using Medium Term time window)
- **Signal Line**: 9-period EMA of MACD line (special configuration)
- **Histogram**: MACD line minus Signal line
- **Application**: Fast Line uses Short Term (12 hours), Slow Line uses Medium Term (2 days)
- **Special Note**: Hybrid approach combining traditional MACD periods with system time windows for optimal ETH market analysis

#### EMA (Exponential Moving Average)
- **Periods**: 12, 48, 192 periods (reusing Time Windows parameters)
- **Price Ratios**: Current price relative to each EMA
- **Application**: Applied to all three timeframes using common Time Windows
- **Purpose**: Trend direction and strength measurement

#### ATR (Average True Range)
- **Window**: 12 periods (aligned with Short Term time window)
- **Purpose**: Volatility measurement and risk assessment
- **Application**: Applied to all three timeframes using common Time Windows
- **Special Note**: Uses 12-period window aligned with Short Term for consistent time frame mapping

### Label Generation
**Classification Labels (1-7)**:
1. **大幅下跌** (< -5% return)
2. **中等下跌** (-5% to -2% return)
3. **小幅下跌** (-2% to -0.5% return)
4. **基本持平** (-0.5% to +0.5% return)
5. **小幅上涨** (+0.5% to +2% return)
6. **中等上涨** (+2% to +5% return)
7. **大幅上涨** (> +5% return)

### Feature Vector Composition
- **Original Features**: 6 (3 RSI + 3 BB Position)
- **Added Features**: 11 (MACD 4 + EMA 3 + ATR 1 + derived features)
- **Total Features**: 17 technical indicators
- **Sequence Length**: 192 periods (longest window)
- **Label Timing**: 24 hours after feature window end

### Feature Categories
1. **Momentum Indicators**: RSI(3), MACD histogram(1) = 4 features
2. **Trend Indicators**: EMA ratios(3), BB position(3) = 6 features
3. **Volatility Indicators**: ATR(1), BB bands(2) = 3 features
4. **Derived Features**: Price ratios, normalized values = 4 features

## 4. Machine Learning Module

### Data Preparation
- **Sampling Strategy**: Configurable stride parameter
- **Train/Validation Split**: 80%/20% chronological split
- **Class Balancing**: Stratified sampling to maintain distribution

### Model Configuration
```python
XGBoost_Params = {
    "objective": "multi:softprob",
    "num_class": 7,
    "max_depth": 6,
    "learning_rate": 0.1,
    "n_estimators": 200,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": 42
}
```

### Evaluation Metrics
- **Primary**: Multi-class accuracy
- **Secondary**: Precision, Recall, F1-score per class
- **Visualization**: Confusion matrix heatmap
- **Performance Charts**: 
  - Training/validation accuracy curves
  - Class-wise precision/recall bars
  - Feature importance ranking

## Implementation Requirements

### Class Structure
```python
# Module 1: Data Collection
OkexDataCollector()
- collect_historical_data(symbol, start_time, end_time)
- save_to_mongodb(collection_name)

# Module 2: Database Interface
MongoDataHandler()
- insert_candles(data_list)
- get_historical_data(symbol, start_time, end_time)
- insert_features(feature_data)

# Module 3: Feature Engineering
FeatureEngineer()
- calculate_technical_indicators(df)
- generate_labels(df)
- create_feature_dataset(df, stride=10)

# Module 4: ML Training
MLTrainer()
- prepare_training_data(stride=10)
- train_model(validation_split=0.2)
- evaluate_model()
- plot_performance_report()
```

### Jupyter Notebook Integration
Each module provides clean notebook interfaces:
```python
# In notebook cells:
from src.collector import OkexDataCollector
collector = OkexDataCollector()
collector.run_collection_job()  # Simple one-liner

from src.trainer import MLTrainer
trainer = MLTrainer()
trainer.execute_full_pipeline(stride=15)  # Customizable parameters
```

### Configuration Management
Environment variables in `.env`:
```
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=eth_options_hunter
OKEX_API_KEY=your_key
OKEX_API_SECRET=your_secret
RATE_LIMIT=20  # requests per second
```

## Performance Targets

### System Requirements
- **Data Throughput**: 7,200 candles/hour processing capacity
- **Storage Efficiency**: ~50MB per year of 1-hour ETH data
- **Model Training**: < 30 minutes for 10,000 samples
- **Memory Usage**: < 2GB peak during feature engineering

### Quality Benchmarks
- **Data Completeness**: > 99.5%
- **Label Accuracy**: 100% (calculated from actual returns)
- **Model Accuracy**: > 55% baseline expectation
- **API Reliability**: > 99% success rate

## Risk Management

### Data Quality Controls
- Missing data detection and interpolation
- Outlier identification and handling
- Duplicate record prevention
- Data freshness monitoring

### Operational Safeguards
- Rate limit compliance monitoring
- Database connection health checks
- Model performance degradation alerts
- Backup and recovery procedures

## Future Enhancements
- Real-time streaming data support
- Additional technical indicators
- Ensemble model combinations
- Backtesting framework integration
- Web dashboard for visualization

---

*This PRD defines the complete specification for the ETH Options Hunter Tool v1.0*