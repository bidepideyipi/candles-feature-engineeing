# PRD.md - Feature Engineering Parameters Reference Document

## 1. Data Sampling Parameters

### Stride Parameter (采样步长)
- **Value**: 10
- **Purpose**: Balance between sample diversity and computational efficiency
- **Rationale**: 
  - Reduces temporal correlation between adjacent samples from 99.7% to 96.7% overlap
  - Effectively filters high-frequency market noise
  - Prevents overfitting while maintaining adequate training data quantity
- **Impact Analysis**:
  ```
  With 53,073 raw records and 300-period feature window + 24-period prediction horizon:
  Stride=1  → 52,749 samples (risk: severe overfitting due to 99.7% data overlap)
  Stride=5  → 10,550 samples (risk: moderate overfitting, 98.3% overlap)  
  Stride=10 → 5,276 samples (optimal balance, 96.7% overlap)
  Stride=15 → 3,517 samples (risk: potential underfitting)
  ```
- **Financial Rationale**: Cryptocurrency hourly data exhibits strong short-term autocorrelation, requiring sufficient spacing between samples
- **Industry Alignment**: Consistent with best practices for hourly cryptocurrency modeling

### Feature Window Size
- **Value**: 300 periods
- **Composition**: Multi-timeframe analysis
  - Short term: 24 periods (1 day)
  - Medium term: 72 periods (3 days)  
  - Long term: 168 periods (1 week)
- **Justification**: Captures comprehensive market dynamics across different time horizons
- **Memory Consideration**: Balances feature richness with computational feasibility

### Prediction Horizon
- **Value**: 24 periods (hours)
- **Reasoning**: Provides meaningful future return calculation window
- **Trade-off**: Longer horizons increase predictive uncertainty but improve signal strength
- **Market Context**: 24-hour horizon aligns with daily trading cycles and institutional reporting

## 2. Technical Indicator Parameters

### RSI Calculation
- **Window**: 14 periods
- **Purpose**: Momentum measurement and trend identification
- **Application**: Calculated for all three timeframes (short, medium, long)
- **Standard Practice**: Industry-standard RSI period for balanced sensitivity

### Bollinger Bands
- **Window**: 20 periods
- **Standard Deviations**: 2
- **Function**: Volatility assessment and price level evaluation
- **Components Generated**:
  - Upper band (BB_Upper)
  - Lower band (BB_Lower)  
  - Middle band (BB_Middle)
  - Band position (0-1 scale)
  - Price to MA ratio

### Price Features
- **Volatility**: 24-hour rolling standard deviation normalized by mean
- **Trend**: 24-hour price change percentage
- **Volume Metrics**: Average volume over feature window
- **Future Return**: Actual return calculation for supervised learning

## 3. Data Quality Parameters

### Minimum Data Requirements
- **Training Phase**: Feature Window + Prediction Horizon + 100 buffer periods
- **Prediction Phase**: Feature Window only (300 periods minimum)
- **Validation**: Stratified cross-validation to maintain class distribution

### Data Integrity Checks
- **Missing Value Handling**: Median imputation for numerical features
- **Duplicate Detection**: Timestamp-based deduplication
- **Outlier Management**: Winsorization at 99th percentile for extreme values

### Database Integration
- **MongoDB Storage**: Persistent candlestick data storage
- **Indexing Strategy**: Timestamp-based indexing for efficient retrieval
- **Connection Pooling**: Managed connections to prevent resource exhaustion

## 4. Performance Optimization Parameters

### Batch Processing Configuration
- **Processing Chunk Size**: Dynamically adjusted based on available memory
- **Parallel Processing**: Disabled for deterministic reproducibility
- **Cache Strategy**: In-memory caching of frequently accessed data segments

### Computational Efficiency
- **Feature Selection**: Automated importance-based feature reduction
- **Memory Management**: Streaming processing for large datasets
- **CPU Utilization**: Single-threaded execution for consistent results

## 5. Model Training Parameters

### XGBoost Hyperparameters
- **n_estimators**: 100 (trees)
- **max_depth**: 6 (tree depth)
- **learning_rate**: 0.1 (shrinkage)
- **subsample**: 0.8 (row sampling)
- **colsample_bytree**: 0.8 (column sampling)

### Validation Strategy
- **Cross-Validation**: 5-fold stratified CV
- **Evaluation Metric**: Multi-class log-loss and accuracy
- **Early Stopping**: Implemented to prevent overfitting

## 6. Deployment Parameters

### API Configuration
- **Rate Limiting**: Token bucket algorithm (20 requests per 2 seconds)
- **Response Timeout**: 30 seconds for data-intensive operations
- **Retry Logic**: Exponential backoff with maximum 3 attempts

### Monitoring Thresholds
- **Data Freshness**: Alert if data older than 2 hours
- **Model Performance**: Accuracy degradation alerts (>5% drop)
- **System Health**: Resource utilization monitoring

---

*This document serves as the authoritative reference for all feature engineering parameters and their design rationale.*