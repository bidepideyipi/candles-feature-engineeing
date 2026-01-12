"""
Flask API for training data generation and management.
Provides endpoints to trigger data fetching and training data generation.
"""

import logging
from flask import Flask, jsonify, request
from datetime import datetime
import threading
from typing import Dict, Any

from ..data.training_data_generator import training_generator
from ..data.okex_fetcher import okex_fetcher
from ..data.mongodb_handler import mongo_handler
from ..config.settings import config

logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Global state for tracking ongoing operations
training_status = {
    'is_running': False,
    'last_run': None,
    'message': 'Ready'
}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'mongodb_connected': mongo_handler.client is not None if mongo_handler.client else False
    })

@app.route('/api/generate-training-data', methods=['POST'])
def generate_training_data():
    """
    Generate training data endpoint.
    Accepts parameters for data generation configuration.
    """
    global training_status
    
    if training_status['is_running']:
        return jsonify({
            'error': 'Training data generation already in progress',
            'status': 'busy'
        }), 423  # Locked
    
    try:
        # Parse request parameters
        data = request.get_json() or {}
        max_records = data.get('max_records', 50000)
        stride = data.get('stride', 10)
        prediction_horizon = data.get('prediction_horizon', 24)
        force_refresh = data.get('force_refresh', False)
        
        logger.info(f"Starting training data generation with parameters: "
                   f"max_records={max_records}, stride={stride}, "
                   f"prediction_horizon={prediction_horizon}, force_refresh={force_refresh}")
        
        # Update status
        training_status['is_running'] = True
        training_status['message'] = 'Generating training data...'
        
        # Run in background thread
        thread = threading.Thread(
            target=_generate_training_data_background,
            args=(max_records, stride, prediction_horizon, force_refresh)
        )
        thread.start()
        
        return jsonify({
            'message': 'Training data generation started',
            'status': 'started',
            'parameters': {
                'max_records': max_records,
                'stride': stride,
                'prediction_horizon': prediction_horizon,
                'force_refresh': force_refresh
            }
        })
        
    except Exception as e:
        training_status['is_running'] = False
        training_status['message'] = f'Error: {str(e)}'
        logger.error(f"Failed to start training data generation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/training-status', methods=['GET'])
def get_training_status():
    """Get current training data generation status."""
    return jsonify(training_status)

@app.route('/api/fetch-historical-data', methods=['POST'])
def fetch_historical_data():
    """
    Fetch historical data from OKEx API.
    Checks MongoDB for existing data to avoid duplicates.
    """
    try:
        data = request.get_json() or {}
        max_records = data.get('max_records', 10000)
        force_refresh = data.get('force_refresh', False)
        
        logger.info(f"Fetching historical data: max_records={max_records}, force_refresh={force_refresh}")
        
        # Fetch data (will check for duplicates automatically)
        historical_data = okex_fetcher.fetch_historical_data(
            max_records=max_records,
            check_duplicates=not force_refresh
        )
        
        if not historical_data:
            if not force_refresh:
                return jsonify({
                    'message': 'Data already exists in MongoDB. Use force_refresh=true to override.',
                    'status': 'skipped',
                    'existing_data': True
                })
            else:
                return jsonify({
                    'message': 'No new data fetched',
                    'status': 'completed',
                    'records_fetched': 0
                })
        
        # Store in MongoDB
        success = mongo_handler.insert_candlestick_data(historical_data)
        
        return jsonify({
            'message': 'Historical data fetch completed',
            'status': 'completed',
            'records_fetched': len(historical_data),
            'stored_successfully': success
        })
        
    except Exception as e:
        logger.error(f"Failed to fetch historical data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-stats', methods=['GET'])
def get_data_stats():
    """Get statistics about stored data."""
    try:
        # Get data statistics from MongoDB
        earliest_timestamp = mongo_handler.get_earliest_timestamp()
        latest_timestamp = mongo_handler.get_latest_timestamp()
        total_records = len(mongo_handler.get_candlestick_data(limit=1000000))
        
        stats = {
            'total_records': total_records,
            'earliest_timestamp': earliest_timestamp,
            'latest_timestamp': latest_timestamp,
            'date_range': None
        }
        
        if earliest_timestamp and latest_timestamp:
            from datetime import datetime
            earliest_dt = datetime.fromtimestamp(earliest_timestamp / 1000)
            latest_dt = datetime.fromtimestamp(latest_timestamp / 1000)
            stats['date_range'] = {
                'from': earliest_dt.isoformat(),
                'to': latest_dt.isoformat(),
                'duration_days': (latest_dt - earliest_dt).days
            }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Failed to get data stats: {e}")
        return jsonify({'error': str(e)}), 500

def _generate_training_data_background(max_records: int, stride: int, 
                                     prediction_horizon: int, force_refresh: bool):
    """Background function for training data generation."""
    global training_status
    
    try:
        training_status['message'] = 'Fetching historical data...'
        
        # Fetch historical data if needed
        if force_refresh or not mongo_handler.get_earliest_timestamp():
            historical_data = okex_fetcher.fetch_historical_data(
                max_records=max_records,
                check_duplicates=not force_refresh
            )
            if historical_data:
                mongo_handler.insert_candlestick_data(historical_data)
                training_status['message'] = f'Fetched {len(historical_data)} records'
            elif not force_refresh:
                training_status['message'] = 'Using existing data from MongoDB'
        
        training_status['message'] = 'Generating training dataset...'
        
        # Generate training dataset
        features_df, targets_series = training_generator.load_existing_training_data(
            stride=stride,
            prediction_horizon=prediction_horizon
        )
        
        training_status['message'] = 'Training data generation completed'
        training_status['last_run'] = datetime.now().isoformat()
        
        logger.info(f"Training data generation completed. "
                   f"Features: {len(features_df)}, Targets: {len(targets_series)}")
        
    except Exception as e:
        training_status['message'] = f'Error: {str(e)}'
        logger.error(f"Training data generation failed: {e}")
    finally:
        training_status['is_running'] = False

def run_api(host: str = '127.0.0.1', port: int = 5000, debug: bool = False):
    """
    Run the Flask API server.
    
    Args:
        host: Host to bind to
        port: Port to listen on
        debug: Whether to run in debug mode
    """
    logger.info(f"Starting API server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    run_api()