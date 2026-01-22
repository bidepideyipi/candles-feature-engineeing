#!/usr/bin/env python3
"""
Main entry point for the Technical Analysis Helper.

Provides command-line interface for:
1. Training the model
2. Making predictions
3. Testing the system
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# 导入重构后的模块
from src.models.xgboost_trainer import xgb_trainer
from src.data.training_data_generator import training_generator
from src.data.okex_fetcher import okex_fetcher
from src.data.mongodb_handler import mongo_handler
from src.utils.feature_engineering import feature_engineer
from src.config.settings import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('technical_analysis.log')
    ]
)

logger = logging.getLogger(__name__)


def _get_prediction_description(predicted_class: int) -> str:
    """Get human-readable description of the prediction."""
    descriptions = {
        -4: "Strong bearish movement (<-2.5%)",
        -3: "Moderate bearish movement (-2.5% to -1.5%)",
        -2: "Light bearish movement (-1.5% to -1.0%)",
        -1: "Very light bearish movement (-1.0% to -0.5%)",
        0: "Neutral movement (-0.5% to 0.5%)",
        1: "Very light bullish movement (0.5% to 1.0%)",
        2: "Light bullish movement (1.0% to 2.5%)",
        3: "Strong bullish movement (>2.5%)"
    }
    return descriptions.get(predicted_class, "Unknown movement")


def setup_environment():
    """Setup environment and check prerequisites."""
    logger.info("Setting up environment...")
    
    # Check if .env file exists
    env_file = Path('.env')
    if not env_file.exists():
        logger.warning(".env file not found. Using default configuration.")
        logger.warning("Copy .env.example to .env and configure your settings.")
    
    # Create necessary directories
    models_dir = Path(config.MODEL_SAVE_PATH).parent
    models_dir.mkdir(exist_ok=True)
    
    logger.info("Environment setup completed.")

def train_model(args):
    """Train and save the model using the decoupled workflow."""
    logger.info("Starting model training using decoupled workflow...")
    
    try:
        # Step 1: Generate training data
        logger.info("Step 1: Generating training data...")
        features_df, targets_series = training_generator.generate_training_data(
            max_records=args.max_records,
            stride=args.stride,
            prediction_horizon=args.prediction_horizon
        )
        
        if features_df.empty:
            raise ValueError("Failed to generate training data")
        
        logger.info(f"Generated {len(features_df)} training samples with {len(features_df.columns)} features")
        
        # Step 2: Train model
        logger.info("Step 2: Training XGBoost model...")
        results = xgb_trainer.train_model(features_df, targets_series)
        
        # Step 3: Display results
        print("\n" + "="*50)
        print("TRAINING RESULTS")
        print("="*50)
        print(f"Accuracy: {results['accuracy']:.4f}")
        print(f"Cross-validation accuracy: {results['cv_mean_accuracy']:.4f} ± {results['cv_std_accuracy']:.4f}")
        print("\nClass Confidence:")
        for class_label, confidence in results['class_confidence'].items():
            print(f"  Class {class_label}: {confidence:.4f}")
        print("="*50)
        
        logger.info("Model training completed successfully")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def make_prediction(args):
    """Make a prediction on current market data using the decoupled workflow."""
    logger.info("Making prediction using decoupled workflow...")
    
    # Load model first
    if not xgb_trainer.load_model():
        logger.error("Failed to load model. Train a model first using --train")
        sys.exit(1)
    
    try:
        # Step 1: Fetch recent data
        logger.info("Step 1: Fetching recent candlestick data")
        recent_raw_data = okex_fetcher.fetch_candlesticks(bar="1H")
        
        if not recent_raw_data:
            logger.error("Failed to fetch recent data")
            sys.exit(1)
        
        # Convert to proper format
        recent_data = okex_fetcher._process_candlestick_data(recent_raw_data)
        
        # Step 2: Get historical data from MongoDB to reach required window size
        logger.info("Step 2: Fetching historical data from MongoDB")
        db_data = mongo_handler.get_candlestick_data(limit=config.FEATURE_WINDOW_SIZE)
        
        # Combine recent and historical data
        all_data = []
        
        # Add historical data (excluding recent duplicates)
        if db_data:
            # Convert MongoDB data to the same format
            for doc in db_data:
                # Skip if timestamp already in recent data
                if not any(candle['timestamp'] == doc['timestamp'] for candle in recent_data):
                    all_data.append({
                        'timestamp': doc['timestamp'],
                        'open': doc['open'],
                        'high': doc['high'],
                        'low': doc['low'],
                        'close': doc['close'],
                        'volume': doc['volume'],
                        'vol_ccy': doc.get('vol_ccy', 0),
                        'vol_ccy_quote': doc.get('vol_ccy_quote', 0),
                        'confirm': doc.get('confirm', 1)
                    })
        
        # Add recent data
        all_data.extend(recent_data)
        
        # Sort by timestamp
        all_data.sort(key=lambda x: x['timestamp'])
        
        logger.info(f"Total data points: {len(all_data)}")
        
        # Step 3: Prepare features
        logger.info("Step 3: Preparing features for prediction")
        features_df = feature_engineer.prepare_prediction_features(all_data)
        
        if features_df is None or features_df.empty:
            logger.error("Failed to prepare features for prediction")
            sys.exit(1)
        
        # Remove timestamp column if present (not used for prediction)
        if 'timestamp' in features_df.columns:
            features_df = features_df.drop('timestamp', axis=1)
        
        # Step 4: Make prediction
        logger.info("Step 4: Making prediction")
        predictions, probabilities = xgb_trainer.predict(features_df)
        
        # Get the prediction and confidence
        predicted_class = int(predictions[0])
        class_probabilities = probabilities[0]
        
        # Get confidence for the predicted class
        # Classes are encoded as 0-7 internally, but represent -4 to 3
        predicted_class_index = predicted_class + 4  # Convert to 0-7 index
        confidence = float(class_probabilities[predicted_class_index])
        
        # Get current price
        current_price = float(all_data[-1]['close'])
        
        # Get price range for the predicted class
        min_range, max_range = config.CLASSIFICATION_THRESHOLDS[predicted_class]
        
        # Create result dictionary
        result = {
            'timestamp': datetime.now().isoformat(),
            'current_price': current_price,
            'predicted_class': predicted_class,
            'confidence': confidence,
            'price_range_min': min_range,
            'price_range_max': max_range,
            'prediction_description': _get_prediction_description(predicted_class),
            'all_probabilities': {
                str(label): float(class_probabilities[label + 4]) 
                for label in sorted(config.CLASSIFICATION_THRESHOLDS.keys())
            }
        }
        
        logger.info(f"Prediction completed: Class {predicted_class} with {confidence:.2%} confidence")
        
        # Display results
        print("\n" + "="*60)
        print("PRICE MOVEMENT PREDICTION")
        print("="*60)
        print(f"Timestamp: {result['timestamp']}")
        print(f"Current Price: ${result['current_price']:.2f}")
        print(f"Predicted Movement: {result['prediction_description']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Expected Range: {result['price_range_min']}% to {result['price_range_max']}%")
        print("\nAll Probabilities:")
        for class_label, prob in result['all_probabilities'].items():
            bar = "█" * int(prob * 20)
            print(f"  Class {class_label:2s}: {prob:6.2%} |{bar:<20}|")
        print("="*60)
            
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def test_system(args):
    """Run system tests."""
    logger.info("Running system tests...")
    
    print("System Test Results:")
    print("-" * 30)
    
    # Test 1: Configuration loading
    try:
        print(f"✓ Configuration loaded (Window size: {config.FEATURE_WINDOW_SIZE})")
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return
    
    # Test 2: Dependencies
    try:
        import xgboost, pandas, numpy, requests
        print("✓ Core dependencies available")
    except ImportError as e:
        print(f"✗ Missing dependencies: {e}")
        return
    
    # Test 3: OKEx API connectivity (optional)
    try:
        from src.data.okex_fetcher import okex_fetcher
        price = okex_fetcher.get_latest_price()
        if price:
            print(f"✓ OKEx API connectivity (Latest ETH price: ${price:.2f})")
        else:
            print("⚠ OKEx API connectivity test inconclusive")
    except Exception as e:
        print(f"⚠ OKEx API test failed: {e}")
    
    # Test 4: MongoDB connection (optional)
    try:
        from src.data.mongodb_handler import mongo_handler
        if mongo_handler.connect():
            print("✓ MongoDB connection successful")
            mongo_handler.close()
        else:
            print("⚠ MongoDB connection failed (check configuration)")
    except Exception as e:
        print(f"⚠ MongoDB test failed: {e}")
    
    print("-" * 30)
    print("System tests completed")

def start_api(args):
    """Start the training data API server."""
    logger.info("Starting API server...")
    
    try:
        from src.api.training_api import run_api
        run_api(host=args.host, port=args.port, debug=args.debug)
    except ImportError as e:
        logger.error(f"Failed to import API module: {e}")
        logger.error("Make sure Flask is installed: pip install flask")
        sys.exit(1)
    except Exception as e:
        logger.error(f"API server failed: {e}")
        sys.exit(1)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Technical Analysis Helper")
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train the model')
    train_parser.add_argument('--max-records', type=int, default=50000, 
                            help='Maximum number of records for training (default: 50000)')
    train_parser.add_argument('--stride', type=int, default=10,
                            help='Stride between training samples (default: 10)')
    train_parser.add_argument('--prediction-horizon', type=int, default=24,
                            help='Prediction horizon in hours (default: 24)')
    
    # Predict command
    predict_parser = subparsers.add_parser('predict', help='Make a prediction')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run system tests')
    
    # API command
    api_parser = subparsers.add_parser('api', help='Start API server')
    api_parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    api_parser.add_argument('--port', type=int, default=5000, help='Port to listen on (default: 5000)')
    api_parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Setup environment
    setup_environment()
    
    # Execute command
    if args.command == 'train':
        train_model(args)
    elif args.command == 'predict':
        make_prediction(args)
    elif args.command == 'test':
        test_system(args)
    elif args.command == 'api':
        start_api(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()