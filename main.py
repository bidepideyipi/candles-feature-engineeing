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

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.models.predictor import predictor
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
    """Train and save the model."""
    logger.info("Starting model training...")
    
    try:
        results = predictor.train_and_save_model(
            max_records=args.max_records,
            stride=args.stride,
            prediction_horizon=args.prediction_horizon
        )
        
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
        sys.exit(1)

def make_prediction(args):
    """Make a prediction on current market data."""
    logger.info("Making prediction...")
    
    # Load model first
    if not predictor.load_model():
        logger.error("Failed to load model. Train a model first using --train")
        sys.exit(1)
    
    try:
        result = predictor.predict_current_movement()
        
        if result:
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
        else:
            logger.error("Prediction failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
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