# Technical Analysis Helper

A Python project that uses XGBoost to predict cryptocurrency price movements based on technical indicators from OKEx exchange.

## Features
- 📊 Fetches candlestick data from OKEx API
- 📈 Calculates technical indicators (RSI, MACD, BOLL) across multiple time windows
- 💾 Stores data in MongoDB for persistence
- 🤖 Trains XGBoost classification model for price movement prediction
- 🔮 Outputs classification with confidence scores
- 🎯 8-class classification system for different price movement ranges

## Classification System
The model predicts price movements in the following categories:

| Class | Description | Price Range |
|-------|-------------|-------------|
| -3 | Strong bearish | < -5.5% |
| -2 | Light bearish | -2.5% to -5.0% |
| -1 | Very light bearish | -0.5% to -2.5% |
| 0 | Neutral | -0.5% to 0.5% |
| 1 | Very light bullish | 0.5% to 2.5% |
| 2 | Light bullish | 2.5% to 5.5% |
| 3 | Strong bullish | > 5.5% |

## Prerequisites
- Python 3.8+
- MongoDB (local or remote)
- Virtual environment (recommended)

## Quick Start

### 1. Setup Environment
```bash
# Clone the repository
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
# Copy and edit the configuration file
cp .env.example .env
```

Edit `.env` with your settings:
```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=technical_analysis
MONGODB_COLLECTION=candlesticks

# Redis Configuration (for rate limiting)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# OKEx API Configuration
OKEX_API_BASE_URL=https://www.okx.com
INST_ID=ETH-USDT-SWAP

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
# Test that all components work correctly
python test_system.py
```

### 5. Train the Model
```bash
# Train with default parameters
python main.py train

# Or customize training parameters
python main.py train --max-records 100000 --stride 5 --prediction-horizon 48
```

### 6. Make Predictions
```bash
# Make a prediction on current market data
python main.py predict
```

### 7. Start API Server (Optional)
```bash
# Start the training data API server
python main.py api

# Or with custom settings
python main.py api --host 0.0.0.0 --port 8000 --debug
```

## Usage Examples

### Command Line Interface
```bash
# Train model with verbose logging
python main.py train --verbose

# Make prediction
python main.py predict

# Run system tests
python main.py test

# Start API server
python main.py api

# Get help
python main.py --help
python main.py train --help
```

### REST API Endpoints

When running the API server (`python main.py api`), the following endpoints are available:

#### `GET /health`
Health check endpoint.
```bash
curl http://localhost:5000/health
```

#### `GET /api/data-stats`
Get statistics about stored data.
```bash
curl http://localhost:5000/api/data-stats
```

#### `POST /api/fetch-historical-data`
Fetch historical data from OKEx API (checks MongoDB for duplicates).
```bash
curl -X POST http://localhost:5000/api/fetch-historical-data \
  -H "Content-Type: application/json" \
  -d '{
    "max_records": 10000,
    "force_refresh": false
  }'
```

#### `POST /api/generate-training-data`
Generate training dataset (runs in background).
```bash
curl -X POST http://localhost:5000/api/generate-training-data \
  -H "Content-Type: application/json" \
  -d '{
    "max_records": 50000,
    "stride": 10,
    "prediction_horizon": 24,
    "force_refresh": false
  }'
```

#### `GET /api/training-status`
Check status of training data generation.
```bash
curl http://localhost:5000/api/training-status
```

### API Testing
```bash
# Test all API endpoints
python test_api.py
```

### Programmatic Usage
```python
from src.models.predictor import predictor

# Train and save model
results = predictor.train_and_save_model(
    max_records=50000,
    stride=10,
    prediction_horizon=24
)

# Load trained model
predictor.load_model()

# Make prediction
prediction = predictor.predict_current_movement()
if prediction:
    print(f"Predicted class: {prediction['predicted_class']}")
    print(f"Confidence: {prediction['confidence']:.2%}")
    print(f"Description: {prediction['prediction_description']}")
```

## Project Structure
```
├── src/
│   ├── config/
│   │   └── settings.py          # Configuration management
│   ├── data/
│   │   ├── mongodb_handler.py   # MongoDB operations
│   │   ├── okex_fetcher.py      # OKEx API client
│   │   └── training_data_generator.py  # Training data pipeline
│   ├── models/
│   │   ├── predictor.py         # Main prediction interface
│   │   └── xgboost_trainer.py   # XGBoost model training
│   └── utils/
│       ├── feature_engineering.py    # Feature creation
│       └── technical_indicators.py   # Technical indicator calculations
├── models/                      # Saved models directory
├── notebooks/                   # Jupyter notebooks
├── tests/                       # Test files
├── main.py                      # Main CLI entry point
├── test_system.py              # System test script
├── requirements.txt            # Python dependencies
├── .env.example               # Configuration template
└── README.md                  # This file
```

## Technical Details

### Data Pipeline
1. **Data Fetching**: Retrieves hourly candlestick data from OKEx API
2. **Storage**: Persists data in MongoDB for historical analysis
3. **Feature Engineering**: 
   - Calculates RSI, MACD, BOLL indicators for short (24h), medium (72h), and long (168h) time windows
   - Creates 300-period sliding windows for training
   - Generates classification labels based on future price movements
4. **Model Training**: Uses XGBoost with multi-class classification
5. **Prediction**: Outputs class prediction with confidence probability

### Model Architecture
- **Algorithm**: XGBoost (Gradient Boosting)
- **Task**: Multi-class classification (7 classes)
- **Features**: 27 technical indicators + price features
- **Validation**: Cross-validation with stratified sampling

### Advanced Features

#### Rate Limiting
- Uses Redis-based token bucket algorithm
- Respects OKEx API limits (20 requests per 2 seconds)
- Automatic retry with exponential backoff

#### Duplicate Detection
- Smart MongoDB integration prevents duplicate data storage
- Checks existing data before fetching new data
- Option to force refresh when needed

#### API Management
- RESTful API for training data generation
- Background processing for long-running tasks
- Real-time status monitoring
- Thread-safe operations

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Ensure MongoDB is running: `mongod`
   - Check connection string in `.env`
   - Verify firewall settings

2. **API Errors**
   - Check internet connectivity
   - Verify OKEx API is accessible
   - Check rate limits

3. **Import Errors**
   - Ensure virtual environment is activated
   - Reinstall dependencies: `pip install -r requirements.txt`

4. **Insufficient Data**
   - Increase `max_records` during training
   - Check OKEx API response

### Debugging
```bash
# Enable verbose logging
python main.py --verbose train

# Check system components
python test_system.py

# Manual debugging
python debug_imports.py
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python test_system.py`
5. Submit a pull request

## License
MIT License - see LICENSE file for details.