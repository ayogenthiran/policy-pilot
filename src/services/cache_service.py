"""
Cache service for Policy Pilot RAG backend.
Handles caching of frequently accessed data with TTL and memory management.
"""

import time
import threading
import hashlib
import json
from typing import Dict, Any, Optional, Union, Callable
from collections import OrderedDict
import psutil

from src.core.logging import get_logger
from src.utils.exceptions import CacheServiceError

logger = get_logger(__name__)


class CacheService:
    """Service for caching frequently accessed data with TTL and memory management."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize the cache service.
        
        Args:
            max_size: Maximum number of items in cache
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = threading.RLock()
        self._memory_threshold = 0.8  # 80% memory usage threshold
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size': 0
        }
        
        logger.info(f"CacheService initialized: max_size={max_size}, default_ttl={default_ttl}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        try:
            with self._lock:
                if key not in self._cache:
                    self._stats['misses'] += 1
                    return None
                
                item = self._cache[key]
                
                # Check if expired
                if time.time() > item['expires_at']:
                    del self._cache[key]
                    self._stats['misses'] += 1
                    self._stats['size'] = len(self._cache)
                    return None
                
                # Move to end (LRU)
                self._cache.move_to_end(key)
                self._stats['hits'] += 1
                
                logger.debug(f"Cache hit for key: {key}")
                return item['value']
                
        except Exception as e:
            logger.error(f"Failed to get from cache: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
            
        Returns:
            True if successful
        """
        try:
            with self._lock:
                # Check memory usage
                self._check_memory_usage()
                
                # Use default TTL if not provided
                if ttl is None:
                    ttl = self.default_ttl
                
                # Create cache item
                item = {
                    'value': value,
                    'expires_at': time.time() + ttl,
                    'created_at': time.time()
                }
                
                # Remove existing key if present
                if key in self._cache:
                    del self._cache[key]
                
                # Add new item
                self._cache[key] = item
                
                # Evict if over capacity
                while len(self._cache) > self.max_size:
                    self._evict_oldest()
                
                self._stats['size'] = len(self._cache)
                logger.debug(f"Cached key: {key} (ttl={ttl}s)")
                return True
                
        except Exception as e:
            logger.error(f"Failed to set cache: {e}")
            return False
    
    def get_or_set(self, key: str, factory: Callable[[], Any], ttl: Optional[int] = None) -> Any:
        """
        Get value from cache or set it using factory function.
        
        Args:
            key: Cache key
            factory: Function to generate value if not in cache
            ttl: Time-to-live in seconds
            
        Returns:
            Cached or generated value
        """
        try:
            # Try to get from cache
            value = self.get(key)
            if value is not None:
                return value
            
            # Generate value using factory
            value = factory()
            
            # Cache the value
            self.set(key, value, ttl)
            
            return value
            
        except Exception as e:
            logger.error(f"Failed to get or set cache: {e}")
            # Return factory result even if caching fails
            return factory()
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted
        """
        try:
            with self._lock:
                if key in self._cache:
                    del self._cache[key]
                    self._stats['size'] = len(self._cache)
                    logger.debug(f"Deleted cache key: {key}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete from cache: {e}")
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        try:
            with self._lock:
                self._cache.clear()
                self._stats['size'] = 0
                logger.info("Cache cleared")
                
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def _evict_oldest(self) -> None:
        """Evict the oldest (least recently used) item."""
        try:
            if self._cache:
                # Remove oldest item (first in OrderedDict)
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats['evictions'] += 1
                logger.debug(f"Evicted cache key: {oldest_key}")
                
        except Exception as e:
            logger.error(f"Failed to evict from cache: {e}")
    
    def _check_memory_usage(self) -> None:
        """Check memory usage and evict if necessary."""
        try:
            memory = psutil.virtual_memory()
            memory_usage = memory.percent / 100
            
            if memory_usage > self._memory_threshold:
                logger.warning(f"High memory usage: {memory.percent:.1f}%, evicting cache")
                
                # Evict 25% of cache
                evict_count = max(1, len(self._cache) // 4)
                for _ in range(evict_count):
                    if self._cache:
                        self._evict_oldest()
                
        except Exception as e:
            logger.warning(f"Failed to check memory usage: {e}")
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        try:
            with self._lock:
                current_time = time.time()
                expired_keys = []
                
                for key, item in self._cache.items():
                    if current_time > item['expires_at']:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self._cache[key]
                
                self._stats['size'] = len(self._cache)
                
                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                
                return len(expired_keys)
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired cache: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            with self._lock:
                hit_rate = 0
                total_requests = self._stats['hits'] + self._stats['misses']
                if total_requests > 0:
                    hit_rate = self._stats['hits'] / total_requests
                
                return {
                    'size': self._stats['size'],
                    'max_size': self.max_size,
                    'hits': self._stats['hits'],
                    'misses': self._stats['misses'],
                    'hit_rate': hit_rate,
                    'evictions': self._stats['evictions'],
                    'memory_usage_percent': psutil.virtual_memory().percent
                }
                
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {'error': str(e)}
    
    def generate_key(self, *args, **kwargs) -> str:
        """
        Generate a cache key from arguments.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Generated cache key
        """
        try:
            # Create a string representation of all arguments
            key_data = {
                'args': args,
                'kwargs': kwargs
            }
            
            # Convert to JSON string and hash
            key_string = json.dumps(key_data, sort_keys=True, default=str)
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            
            return key_hash
            
        except Exception as e:
            logger.error(f"Failed to generate cache key: {e}")
            # Fallback to simple string representation
            return str(hash(str(args) + str(kwargs)))
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on cache service.
        
        Returns:
            Health check results
        """
        try:
            # Test basic operations
            test_key = "health_check_test"
            test_value = "test_value"
            
            # Test set
            set_success = self.set(test_key, test_value, ttl=1)
            
            # Test get
            retrieved_value = self.get(test_key)
            get_success = retrieved_value == test_value
            
            # Clean up
            self.delete(test_key)
            
            # Get stats
            stats = self.get_stats()
            
            return {
                'status': 'healthy' if set_success and get_success else 'unhealthy',
                'set_success': set_success,
                'get_success': get_success,
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"Cache service health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }


# Global cache instance
cache_service = CacheService()
