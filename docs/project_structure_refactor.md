# Project Structure Refactoring Documentation

## New Directory Structure

The project has been reorganized to better separate concerns:

```
src/
├── __init__.py
├── collect/                    # Data collection and storage
│   ├── __init__.py
│   ├── mongodb_handler.py      # MongoDB operations
│   ├── okex_fetcher.py         # OKEx API data fetching
│   └── training_data_generator.py  # Training data orchestration
├── config/
│   └── settings.py             # Configuration settings
├── feature/                    # Feature engineering and processing
│   ├── __init__.py
│   ├── feature_engineering.py  # Main feature engineering pipeline
│   └── technical_indicators.py # Technical indicators calculation
└── models/
    └── xgboost_trainer.py      # Model training and prediction
```

## Directory Responsibilities

### `src/collect/`
Handles all data collection and storage operations:
- **mongodb_handler.py**: Database operations, data persistence
- **okex_fetcher.py**: API data fetching, rate limiting
- **training_data_generator.py**: Orchestrates the complete data pipeline

### `src/feature/`
Handles all feature engineering and technical analysis:
- **feature_engineering.py**: Main feature creation pipeline
- **technical_indicators.py**: Technical indicators calculation (RSI, MACD, BOLL, etc.)

### Other Directories
- **src/config/**: Configuration management
- **src/models/**: Machine learning model training and prediction

## Migration Summary

### Files Moved:
1. `src/data/mongodb_handler.py` → `src/collect/mongodb_handler.py`
2. `src/data/okex_fetcher.py` → `src/collect/okex_fetcher.py`
3. `src/data/training_data_generator.py` → `src/collect/training_data_generator.py`
4. `src/utils/feature_engineering.py` → `src/feature/feature_engineering.py`
5. `src/utils/technical_indicators.py` → `src/feature/technical_indicators.py`

### Import Updates:
All import statements have been updated to reflect the new structure:
- `from ..data.mongodb_handler` → `from ..collect.mongodb_handler`
- `from ..data.okex_fetcher` → `from ..collect.okex_fetcher`
- `from ..utils.feature_engineering` → `from ..feature.feature_engineering`
- `from ..utils.technical_indicators` → `from ..feature.technical_indicators`

## Benefits

1. **Clear Separation of Concerns**: 
   - Data collection/storage logic separated from feature engineering
   - Better modularity and maintainability

2. **Logical Organization**:
   - `collect/` focuses on data acquisition and persistence
   - `feature/` focuses on data transformation and analysis

3. **Scalability**:
   - Easy to add new data sources in `collect/`
   - Easy to add new feature engineering techniques in `feature/`

4. **Reduced Coupling**:
   - Clear boundaries between data handling and feature processing
   - Easier to test individual components

## Usage Examples

```python
# Data collection
from src.collect.okex_fetcher import okex_fetcher
from src.collect.mongodb_handler import mongo_handler

# Feature engineering
from src.feature.feature_engineering import feature_engineer
from src.feature.technical_indicators import tech_calculator

# Training data generation
from src.collect.training_data_generator import training_generator
```

The refactored structure maintains all existing functionality while providing better organization and scalability for future development.