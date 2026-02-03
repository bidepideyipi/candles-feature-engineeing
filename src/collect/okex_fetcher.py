"""
OKEx API client for fetching candlestick data.
"""

import logging
from typing import List, Dict, Any, Optional
import requests
import pymongo
import pandas as pd
from datetime import datetime

from config.settings import config
from utils.rate_limiter import rate_limiter
from .candlestick_handler import candlestick_handler
import pandas as pd

logger = logging.getLogger(__name__)

class OKExDataFetcher:
    """Fetches candlestick data from OKEx API."""
    
    def __init__(self):
        """Initialize OKEx API client."""
        self.base_url = config.OKEX_API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'TechnicalAnalysisHelper/1.0'
        })
    
    # 获取最近的 K 线数据（默认是100条）
    def fetch_candlesticks(self, inst_id: str = None, bar: str = "1H", after: Optional[str] = None) -> List[List[str]]:
        """
        Fetch candlestick data from OKEx API.
        
        Args:
            inst_id: Instrument ID (e.g., "ETH-USDT-SWAP", "BTC-USDT-SWAP")
            bar: Time interval (e.g., "1H", "4H", "1D")
            after: Timestamp to fetch data before this time (for pagination)
            
        Returns:
            List of candlestick data arrays
        """
        endpoint = "/api/v5/market/history-candles"
        url = f"{self.base_url}{endpoint}"
        
        # Use provided inst_id or default ETH-USDT-SWAP
        instrument_id = inst_id or 'ETH-USDT-SWAP'
        
        params = {
            "instId": instrument_id,
            "bar": bar,
            "limit": 300
        }
        
        if after:
            params["after"] = after
            
        logger.info(f"Fetching candlesticks: instId={instrument_id}, bar={bar}, after={after}")
        
        try:
            # Apply rate limiting
            rate_limiter.acquire_token("okex_api")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("code") == "0":
                candle_data = data.get("data", [])
                logger.info(f"Fetched {len(candle_data)} candlestick records")
                return candle_data
            else:
                error_msg = data.get("msg", "Unknown error")
                logger.error(f"API error: {error_msg}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    # 拉取历史数据写入mongodb
    def fetch_historical_data(self, inst_id: str = None, bar: str = "1H", max_records: int = 100000, current_after: int = None) -> bool:
        """
        Fetch historical candlestick data and write to MongoDB.
        Main responsibility is to persist API data to MongoDB.
        
        Args:
            inst_id: Instrument ID (e.g., "ETH-USDT-SWAP")
            bar: Time interval (e.g., "1m", "5m", "15m", "1H", "4H", "1D")
            max_records: Maximum number of records to fetch
            check_duplicates: Whether to check MongoDB for existing data
            
        Returns:
            bool: True if data fetch and storage successful, False otherwise
        """
        
        records_fetched = 0
        total_saved = 0
        
        # Check for existing data if requested
        # if check_duplicates:
        #     earliest_timestamp = candlestick_handler.get_earliest_timestamp(inst_id=inst_id, bar=bar)
        #     latest_timestamp = candlestick_handler.get_latest_timestamp(inst_id=inst_id, bar=bar)
            
        #     if earliest_timestamp and latest_timestamp:
        #         logger.info(f"Found existing {bar} data for {inst_id} in MongoDB: {earliest_timestamp} to {latest_timestamp}")
        #         logger.info("Skipping data fetch as data already exists")
        #         return True  # Return True as data already exists
        
        logger.info(f"Starting historical data fetch and storage, max records: {max_records}")
        
        while records_fetched < max_records:
            raw_data = self.fetch_candlesticks(inst_id=inst_id, bar=bar, after=current_after)
            
            if not raw_data:
                logger.info("No more data available")
                break
            
            # Convert raw data to dictionaries
            processed_data = self._process_candlestick_data(raw_data, inst_id=inst_id, bar=bar)
            
            if processed_data:
                # Save to MongoDB
                save_success = self._save_to_mongodb(processed_data)
                if save_success:
                    total_saved += len(processed_data)
                    logger.info(f"Saved batch of {len(processed_data)} records to MongoDB")
                else:
                    logger.error("Failed to save data batch to MongoDB")
                    return False
            
            records_fetched += len(raw_data)
            logger.info(f"Total records processed: {records_fetched}, Total saved: {total_saved}")
            
            # Set after parameter for next request (use earliest timestamp)
            if processed_data:
                current_after = str(min(item['timestamp'] for item in processed_data) - 1)
            
            # Break if we got less than 100 records (indicates no more historical data)
            if len(raw_data) < 100:
                logger.info("Reached end of available historical data")
                break
            
            # Rate limiting handled by fetch_candlesticks method
        
        logger.info(f"Historical data fetch and storage completed. Total records saved: {total_saved}")
        return True
    
    #处理数据格式
    def _process_candlestick_data(self, raw_data: List[List[str]], inst_id: str = None, bar: str = "1H") -> List[Dict[str, Any]]:
        """
        Process raw candlestick data into structured dictionaries.
        
        Args:
            raw_data: Raw candlestick data from API
            inst_id: Instrument ID for the data (e.g., "ETH-USDT-SWAP")
            bar: Time interval (e.g., "1m", "5m", "15m", "1H", "4H", "1D")
            
        Returns:
            List of processed candlestick dictionaries
        """
        processed = []
        
        for candle in raw_data:
            try:
                # OKEx candlestick data format:
                # [timestamp, open, high, low, close, volume, volCcy, volCcyQuote, confirm]
                # Convert timestamp to datetime
                timestamp = int(candle[0])
                dt = datetime.fromtimestamp(timestamp / 1000)  # Convert milliseconds to seconds
                
                processed.append({
                    'timestamp': timestamp,  # milliseconds
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5]),
                    'vol_ccy': float(candle[6]),
                    'vol_ccy_quote': float(candle[7]),
                    'confirm': int(candle[8]),
                    'inst_id': inst_id or 'ETH-USDT-SWAP',  # Add instrument ID
                    'bar': bar,  # Add time interval
                    'record_dt': dt.strftime('%Y-%m-%d'),  # yyyy-MM-dd format
                    'record_hour': dt.hour,  # Extract hour
                    'day_of_week': dt.weekday()  # Extract day of week (0=Monday, 6=Sunday)
                })
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to process candlestick data: {candle}, error: {e}")
                continue
        
        return processed
    
    def _save_to_mongodb(self, data: List[Dict[str, Any]]) -> bool:
        """
        Save processed data to MongoDB with upsert capability.
        
        Args:
            data: List of processed candlestick dictionaries
            
        Returns:
            bool: True if save successful, False otherwise
        """
        if not data:
            logger.info("No data to save to MongoDB")
            return True
        
        try:            
            # Batch upsert operation using composite key (inst_id + bar + timestamp)
            bulk_operations = []
            for record in data:
                bulk_operations.append(
                    pymongo.UpdateOne(
                        {
                            "inst_id": record["inst_id"],
                            "bar": record["bar"],
                            "timestamp": record["timestamp"]
                        },
                        {"$set": record},
                        upsert=True
                    )
                )
            
            if bulk_operations:
                result = candlestick_handler._get_collection().bulk_write(bulk_operations)
                if result.upserted_count > 0 or result.modified_count > 0:
                    logger.info(f" New records {result.upserted_count}, Matched {result.matched_count}, modified {result.modified_count} existing records")
                else:
                    logger.info(f"No records were upserted or modified (data already exists and is identical)")
                return True
            
        except Exception as e:
            logger.error(f"Failed to save data to MongoDB: {e}")
            return False
    
    #从数据库取出数据转换为DataFrame格式
    def get_all_data_as_df(self) -> Optional[pd.DataFrame]:
        """
        Retrieve all candlestick data from MongoDB and convert to DataFrame.
        Purpose is to prepare data for tech_calculator.calculate_indicators(df).
        
        Returns:
            pandas.DataFrame: All candlestick data sorted by timestamp, 
                             or None if retrieval fails
        """
        try:
            
            # Get all data from MongoDB for ETH-USDT-SWAP
            db_data = candlestick_handler.get_candlestick_data(limit=1000000, inst_id="ETH-USDT-SWAP")  # Large limit to get all data
            
            if not db_data:
                logger.warning("No data found in MongoDB")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(db_data)
            
            # Sort by timestamp ascending (oldest first)
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Convert timestamp to datetime for better handling
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            logger.info(f"Retrieved {len(df)} records from MongoDB for technical analysis")
            return df
            
        except Exception as e:
            logger.error(f"Failed to retrieve data from MongoDB: {e}")
            return None
    
    def get_latest_price(self) -> Optional[float]:
        """
        Get the latest closing price.
        
        Returns:
            Latest closing price or None if fetch fails
        """
        data = self.fetch_candlesticks(inst_id="ETH-USDT-SWAP", bar="1H", after=None)
        if data and len(data) > 0:
            return float(data[0][4])  # close price
        return None

# Global instance
okex_fetcher = OKExDataFetcher()