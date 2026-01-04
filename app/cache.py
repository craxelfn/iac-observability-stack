"""
Redis caching utilities for MasterProject.
Implements cache-aside pattern with automatic serialization and TTL management.
"""

import os
import json
import redis
from typing import Optional, Any, Callable
from functools import wraps
import logging

logger = logging.getLogger("masterproject.cache")

# Redis configuration from environment
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_SSL = os.getenv("REDIS_SSL", "false").lower() == "true"
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "true").lower() == "true"

# Initialize Redis client
redis_client = None

if REDIS_ENABLED:
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=0,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            ssl=REDIS_SSL,
            ssl_cert_reqs=None if REDIS_SSL else None,
        )
        # Test connection
        redis_client.ping()
        logger.info(f"Redis connected: {REDIS_HOST}:{REDIS_PORT}")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Caching disabled.")
        redis_client = None


# ============================================================================
# Cache Metrics
# ============================================================================
class CacheMetrics:
    """Track cache hit/miss metrics."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0
    
    def record_hit(self):
        self.hits += 1
    
    def record_miss(self):
        self.misses += 1
    
    def record_error(self):
        self.errors += 1
    
    def get_hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    def get_stats(self) -> dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "hit_rate": round(self.get_hit_rate(), 2),
            "total_requests": self.hits + self.misses,
        }
    
    def reset(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0


# Global metrics instance
cache_metrics = CacheMetrics()


#  ============================================================================
# Core Cache Functions
# ============================================================================

def get_cache(key: str) -> Optional[Any]:
    """
    Get value from cache.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None if not found/error
    """
    if not redis_client:
        return None
    
    try:
        value = redis_client.get(key)
        if value:
            cache_metrics.record_hit()
            logger.debug(f"Cache HIT: {key}")
            return json.loads(value)
        else:
            cache_metrics.record_miss()
            logger.debug(f"Cache MISS: {key}")
            return None
    except Exception as e:
        cache_metrics.record_error()
        logger.error(f"Cache GET error for {key}: {e}")
        return None


def set_cache(key: str, value: Any, ttl: int = 300):
    """
    Set value in cache with TTL.
    
    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        ttl: Time to live in seconds (default: 5 minutes)
    """
    if not redis_client:
        return False
    
    try:
        serialized = json.dumps(value)
        redis_client.setex(key, ttl, serialized)
        logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
        return True
    except Exception as e:
        cache_metrics.record_error()
        logger.error(f"Cache SET error for {key}: {e}")
        return False


def delete_cache(key: str):
    """Delete value from cache."""
    if not redis_client:
        return False
    
    try:
        redis_client.delete(key)
        logger.debug(f"Cache DELETE: {key}")
        return True
    except Exception as e:
        logger.error(f"Cache DELETE error for {key}: {e}")
        return False


def clear_cache():
    """Clear all cache entries."""
    if not redis_client:
        return False
    
    try:
        redis_client.flushdb()
        logger.info("Cache cleared")
        return True
    except Exception as e:
        logger.error(f"Cache CLEAR error: {e}")
        return False


# ============================================================================
# Cache Decorator
# ============================================================================

def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
        
    Usage:
        @cached(ttl=300, key_prefix="product")
        def get_product(product_id):
            return database.get_product(product_id)
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = get_cache(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Cache miss - call function
            result = func(*args, **kwargs)
            
            # Store in cache
            if result is not None:
                set_cache(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


# ============================================================================
# Cache Helpers
# ============================================================================

def get_cache_stats() -> dict:
    """Get current cache statistics."""
    stats = cache_metrics.get_stats()
    
    if redis_client:
        try:
            info = redis_client.info()
            stats["redis_info"] = {
                "used_memory_human": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            logger.error(f"Failed to get Redis info: {e}")
    
    return stats


def check_cache_connection() -> bool:
    """Check if Redis connection is working."""
    if not redis_client:
        return False
    
    try:
        redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis ping failed: {e}")
        return False
