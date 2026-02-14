#!/usr/bin/env python3
"""
Main entry point for the Technical Analysis Helper API.
Starts the FastAPI server and scheduled prediction tasks.
"""
import argparse
import sys
import logging
import threading
from pathlib import Path
import uvicorn

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.api_base import app
from schedule.prediction_scheduler import prediction_scheduler
from config.settings import config

# Create logger
logger = logging.getLogger(__name__)

# Only configure logging if not already configured
if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """Main entry point to start the FastAPI server."""
    parser = argparse.ArgumentParser(description="Technical Analysis Helper API")
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8000, help='Port to listen on (default: 8000)')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload for development')
    
    args = parser.parse_args()
    
    print(f"Starting Technical Analysis Helper API...")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Auto-reload: {args.reload}")
    print(f"Scheduled task: {'Enabled' if config.SCHEDULE_ENABLED else 'Disabled'}")
    if config.SCHEDULE_ENABLED:
        print(f"  Interval: {config.SCHEDULE_INTERVAL} minutes")
        print(f"  Recipient: {config.SCHEDULE_RECIPIENT}")
        print(f"  Data source: {config.SCHEDULE_DATA_SOURCE}")
    print()
    print("API documentation:")
    print(f"- http://{args.host}:{args.port}/docs")
    print(f"- http://{args.host}:{args.port}/redoc")
    print()
    
    # Start scheduled prediction task in background thread
    schedule_thread = None
    if config.SCHEDULE_ENABLED:
        schedule_thread = threading.Thread(target=prediction_scheduler.run, daemon=False)
        schedule_thread.start()
        logger.info("Scheduled prediction task started in background thread")
    
    try:
        # Start FastAPI server
        uvicorn.run(
            "api.api_base:app",
            host=args.host,
            port=args.port,
            reload=args.reload
        )
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    finally:
        if schedule_thread and schedule_thread.is_alive():
            logger.info("Waiting for scheduled task to stop...")
            schedule_thread.join(timeout=5)
        logger.info("Shutdown complete")


if __name__ == '__main__':
    main()
