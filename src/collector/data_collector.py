"""
OKEx API data collector with rate limiting and error handling.
"""

import logging
import time
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..config.settings import config
from ..utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class OkexDataCollector:
    """
    Collects historical and real-time candlestick data from OKEx API.
    Implements rate limiting, error handling, and data validation.
    """
    
    def __init__(self):
        """
        Initialize the OKEx data collector.
        """
        self.api_base_url = config.OKEX_API_BASE_URL
        self.inst_id = config.INST_ID
        self.rate_limiter = RateLimiter(max_requests=20, time_window=1)
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def collect_historical_data(self, symbol: str, start_time: str, end_time: str, bar: str = '1H') -> List[Dict[str, Any]]:
        """
        Collect historical candlestick data from OKEx API.
        
        Args:
            symbol: Trading symbol (e.g., 'ETH-USDT-SWAP')
            start_time: Start time in ISO format
            end_time: End time in ISO format
            bar: Time interval (e.g., '1H' for 1 hour)
            
        Returns:
            List of candlestick data dictionaries
        """
        logger.info(f"Collecting historical data for {symbol} from {start_time} to {end_time}")
        
        all_data = []
        current_start = start_time
        
        while current_start < end_time:
            try:
                # Rate limiting
                self.rate_limiter.wait()
                
                # API request
                url = f"{self.api_base_url}/api/v5/market/history-candles"
                params = {
                    'instId': symbol,
                    'bar': bar,
                    'after': current_start,
                    'before': end_time,
                    'limit': '100'
                }
                
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('code') != '0':
                    logger.error(f"API error: {data.get('msg')}")
                    continue
                
                candles = data.get('data', [])
                if not candles:
                    break
                
                # Process candles
                processed_candles = []
                for candle in candles:
                    timestamp, open_p, high, low, close, volume, quote_volume = candle
                    processed_candles.append({
                        'timestamp': int(timestamp),
                        'open': float(open_p),
                        'high': float(high),
                        'low': float(low),
                        'close': float(close),
                        'volume': float(volume),
                        'quote_volume': float(quote_volume)
                    })
                
                all_data.extend(processed_candles)
                
                # Update current start time
                last_timestamp = processed_candles[-1]['timestamp']
                current_start = str(last_timestamp + 1)
                
                logger.debug(f"Collected {len(processed_candles)} candles, total: {len(all_data)}")
                
                # Rate limiter handles the timing
                
            except Exception as e:
                logger.error(f"Error collecting data: {e}")
                continue
        
        logger.info(f"Successfully collected {len(all_data)} candles for {symbol}")
        return all_data
    
    def collect_recent_data(self, symbol: str, bar: str = '1H', limit: int = 100) -> List[Dict[str, Any]]:
        """
        Collect recent candlestick data.
        
        Args:
            symbol: Trading symbol
            bar: Time interval
            limit: Number of candles to collect
            
        Returns:
            List of recent candlestick data
        """
        logger.info(f"Collecting {limit} recent candles for {symbol}")
        
        try:
            self.rate_limiter.wait()
            
            url = f"{self.api_base_url}/api/v5/market/history-candles"
            params = {
                'instId': symbol,
                'bar': bar,
                'limit': str(limit)
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') != '0':
                logger.error(f"API error: {data.get('msg')}")
                return []
            
            candles = data.get('data', [])
            processed_candles = []
            
            for candle in candles:
                timestamp, open_p, high, low, close, volume, quote_volume = candle
                processed_candles.append({
                    'timestamp': int(timestamp),
                    'open': float(open_p),
                    'high': float(high),
                    'low': float(low),
                    'close': float(close),
                    'volume': float(volume),
                    'quote_volume': float(quote_volume)
                })
            
            logger.info(f"Successfully collected {len(processed_candles)} recent candles")
            return processed_candles
            
        except Exception as e:
            logger.error(f"Error collecting recent data: {e}")
            return []
    
    def run_collection_job(self, symbol: str = 'ETH-USDT-SWAP', days: int = 365) -> List[Dict[str, Any]]:
        """
        Run a full data collection job for the specified period.
        
        Args:
            symbol: Trading symbol
            days: Number of days to collect
            
        Returns:
            List of collected candlestick data
        """
        logger.info(f"Starting data collection job for {symbol} (last {days} days)")
        
        end_time = datetime.now().isoformat()
        start_time = (datetime.now() - timedelta(days=days)).isoformat()
        
        all_data = self.collect_historical_data(symbol, start_time, end_time)
        
        logger.info(f"Data collection job completed. Total candles: {len(all_data)}")
        return all_data

# Global instance
data_collector = OkexDataCollector()