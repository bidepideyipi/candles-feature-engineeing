"""
Redis-based rate limiter for API calls.
Implements token bucket algorithm to respect OKEx API rate limits (20 requests per 2 seconds).
"""

import time
import logging
from typing import Optional
import redis
from redis.exceptions import RedisError, ConnectionError

from ..config.settings import config

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter using Redis to enforce API rate limits."""
    
    def __init__(self, 
                 redis_host: str = config.REDIS_HOST,
                 redis_port: int = config.REDIS_PORT,
                 redis_db: int = config.REDIS_DB,
                 max_tokens: int = 20,  # OKEx limit: 20 requests per 2 seconds
                 refill_interval: float = 2.0,  # 2 seconds
                 key_prefix: str = "rate_limit"):
        """
        Initialize rate limiter.
        
        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            redis_db: Redis database number
            max_tokens: Maximum number of tokens (requests) allowed
            refill_interval: Time interval to refill tokens (seconds)
            key_prefix: Prefix for Redis keys
        """
        self.redis_client: Optional[redis.Redis] = None
        self.max_tokens = max_tokens
        self.refill_interval = refill_interval
        self.key_prefix = key_prefix
        
        # Connect to Redis
        self._connect_redis(redis_host, redis_port, redis_db)
    
    def _connect_redis(self, host: str, port: int, db: int) -> bool:
        """Connect to Redis server."""
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {host}:{port}")
            return True
        except (ConnectionError, RedisError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
            return False
    
    def _get_key(self, identifier: str) -> str:
        """Generate Redis key for given identifier."""
        return f"{self.key_prefix}:{identifier}"
    
    def acquire_token(self, identifier: str = "okex_api") -> bool:
        """
        Acquire a token for API request. Blocks if no tokens available.
        
        Args:
            identifier: Unique identifier for the rate limit bucket
            
        Returns:
            bool: True if token acquired, False if Redis connection failed
        """
        if not self.redis_client:
            logger.warning("Redis not available, skipping rate limiting")
            return True
        
        key = self._get_key(identifier)
        current_time = time.time()
        
        try:
            # Lua script for atomic token acquisition
            lua_script = """
            local key = KEYS[1]
            local max_tokens = tonumber(ARGV[1])
            local refill_interval = tonumber(ARGV[2])
            local current_time = tonumber(ARGV[3])
            
            -- Get current state
            local tokens = redis.call('HGET', key, 'tokens')
            local last_refill = redis.call('HGET', key, 'last_refill')
            
            -- Initialize if first time
            if not tokens then
                tokens = max_tokens
                last_refill = current_time
                redis.call('HMSET', key, 'tokens', tokens, 'last_refill', last_refill)
                redis.call('EXPIRE', key, 300)  -- Expire after 5 minutes of inactivity
            else
                tokens = tonumber(tokens)
                last_refill = tonumber(last_refill)
                
                -- Refill tokens based on elapsed time
                local elapsed = current_time - last_refill
                local new_tokens = math.floor(elapsed / refill_interval * max_tokens)
                
                if new_tokens > 0 then
                    tokens = math.min(max_tokens, tokens + new_tokens)
                    last_refill = current_time
                    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', last_refill)
                end
            end
            
            -- Try to consume one token
            if tokens >= 1 then
                redis.call('HINCRBY', key, 'tokens', -1)
                return 1
            else
                -- Return time to wait for next token
                local wait_time = refill_interval / max_tokens
                return -wait_time
            end
            """
            
            result = self.redis_client.eval(
                lua_script, 
                1,  # Number of keys
                key,  # KEYS[1]
                self.max_tokens,  # ARGV[1]
                self.refill_interval,  # ARGV[2]
                current_time  # ARGV[3]
            )
            
            if result == 1:
                # Token acquired
                return True
            else:
                # Need to wait
                wait_time = abs(float(result))
                logger.debug(f"Rate limit reached, waiting {wait_time:.3f}s")
                time.sleep(wait_time)
                return self.acquire_token(identifier)  # Retry
                
        except RedisError as e:
            logger.error(f"Redis error in rate limiter: {e}")
            return True  # Continue without rate limiting on Redis error
    
    def get_available_tokens(self, identifier: str = "okex_api") -> int:
        """
        Get number of currently available tokens.
        
        Args:
            identifier: Rate limit bucket identifier
            
        Returns:
            int: Number of available tokens
        """
        if not self.redis_client:
            return self.max_tokens
        
        key = self._get_key(identifier)
        try:
            tokens = self.redis_client.hget(key, 'tokens')
            return int(tokens) if tokens else self.max_tokens
        except RedisError as e:
            logger.error(f"Redis error getting tokens: {e}")
            return self.max_tokens

# Global rate limiter instance
rate_limiter = RateLimiter()