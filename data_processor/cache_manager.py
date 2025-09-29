"""
Cache management for improved performance
"""
import json
import pickle
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import redis
from config.settings import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class CacheManager:
    """Manage caching for price data and calculations"""
    
    def __init__(self):
        self.config = Config()
        self.redis_client = None
        self.memory_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'errors': 0
        }
        
        # Initialize Redis if available
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT,
                db=self.config.REDIS_DB,
                password=self.config.REDIS_PASSWORD,
                decode_responses=False,  # We'll handle encoding manually
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
            
        except Exception as e:
            logger.warning(f"Redis not available, using memory cache only: {e}")
            self.redis_client = None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set cache value with optional TTL (time to live) in seconds"""
        try:
            serialized_value = self._serialize_value(value)
            
            if self.redis_client:
                # Use Redis
                result = self.redis_client.setex(
                    name=self._format_key(key),
                    time=ttl,
                    value=serialized_value
                )
                success = bool(result)
            else:
                # Use memory cache
                expiry_time = datetime.utcnow() + timedelta(seconds=ttl)
                self.memory_cache[key] = {
                    'value': serialized_value,
                    'expiry': expiry_time
                }
                success = True
            
            if success:
                self.cache_stats['sets'] += 1
            
            return success
            
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            self.cache_stats['errors'] += 1
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        try:
            if self.redis_client:
                # Use Redis
                serialized_value = self.redis_client.get(self._format_key(key))
            else:
                # Use memory cache
                cache_entry = self.memory_cache.get(key)
                if cache_entry:
                    if datetime.utcnow() > cache_entry['expiry']:
                        # Expired
                        del self.memory_cache[key]
                        serialized_value = None
                    else:
                        serialized_value = cache_entry['value']
                else:
                    serialized_value = None
            
            if serialized_value is not None:
                self.cache_stats['hits'] += 1
                return self._deserialize_value(serialized_value)
            else:
                self.cache_stats['misses'] += 1
                return None
                
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            self.cache_stats['errors'] += 1
            self.cache_stats['misses'] += 1
            return None
    
    def delete(self, key: str) -> bool:
        """Delete cached value"""
        try:
            if self.redis_client:
                result = self.redis_client.delete(self._format_key(key))
                success = bool(result)
            else:
                success = self.memory_cache.pop(key, None) is not None
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            self.cache_stats['errors'] += 1
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if self.redis_client:
                return bool(self.redis_client.exists(self._format_key(key)))
            else:
                if key in self.memory_cache:
                    if datetime.utcnow() > self.memory_cache[key]['expiry']:
                        del self.memory_cache[key]
                        return False
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Error checking cache key existence {key}: {e}")
            return False
    
    def clear(self, pattern: str = None) -> bool:
        """Clear cache entries matching pattern"""
        try:
            if self.redis_client:
                if pattern:
                    keys = self.redis_client.keys(self._format_key(pattern))
                    if keys:
                        return bool(self.redis_client.delete(*keys))
                else:
                    return bool(self.redis_client.flushdb())
            else:
                if pattern:
                    keys_to_delete = [k for k in self.memory_cache.keys() if pattern in k]
                    for key in keys_to_delete:
                        del self.memory_cache[key]
                else:
                    self.memory_cache.clear()
                return True
                
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_or_set(self, key: str, callback, ttl: int = 3600) -> Any:
        """Get value from cache or compute and cache it"""
        value = self.get(key)
        
        if value is None:
            try:
                value = callback()
                if value is not None:
                    self.set(key, value, ttl)
            except Exception as e:
                logger.error(f"Error in cache callback for key {key}: {e}")
                return None
        
        return value
    
    def cache_price_calculation(self, product_id: int, calculation_type: str, result: Dict, ttl: int = 1800):
        """Cache price calculation results"""
        key = f"price_calc:{product_id}:{calculation_type}"
        self.set(key, result, ttl)
    
    def get_cached_price_calculation(self, product_id: int, calculation_type: str) -> Optional[Dict]:
        """Get cached price calculation"""
        key = f"price_calc:{product_id}:{calculation_type}"
        return self.get(key)
    
    def cache_product_data(self, site_name: str, products: List[Dict], ttl: int = 3600):
        """Cache scraped product data"""
        key = f"products:{site_name}"
        data = {
            'timestamp': datetime.utcnow().isoformat(),
            'count': len(products),
            'products': products
        }
        self.set(key, data, ttl)
    
    def get_cached_product_data(self, site_name: str, max_age_hours: int = 1) -> Optional[List[Dict]]:
        """Get cached product data if recent enough"""
        key = f"products:{site_name}"
        data = self.get(key)
        
        if data and 'timestamp' in data:
            timestamp = datetime.fromisoformat(data['timestamp'])
            age_hours = (datetime.utcnow() - timestamp).total_seconds() / 3600
            
            if age_hours <= max_age_hours:
                return data.get('products', [])
        
        return None
    
    def cache_site_status(self, site_name: str, status: Dict, ttl: int = 600):
        """Cache site availability status"""
        key = f"site_status:{site_name}"
        self.set(key, status, ttl)
    
    def get_cached_site_status(self, site_name: str) -> Optional[Dict]:
        """Get cached site status"""
        key = f"site_status:{site_name}"
        return self.get(key)
    
    def cache_category_stats(self, stats: Dict, ttl: int = 7200):
        """Cache category statistics"""
        key = "category_stats"
        self.set(key, stats, ttl)
    
    def get_cached_category_stats(self) -> Optional[Dict]:
        """Get cached category statistics"""
        key = "category_stats"
        return self.get(key)
    
    def _format_key(self, key: str) -> str:
        """Format cache key with prefix"""
        return f"automotive_prices:{key}"
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for cache storage"""
        try:
            # Try JSON first for simple types
            if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                return json.dumps(value, ensure_ascii=False).encode('utf-8')
            else:
                # Use pickle for complex objects
                return pickle.dumps(value)
        except Exception as e:
            logger.error(f"Error serializing cache value: {e}")
            raise
    
    def _deserialize_value(self, serialized_value: bytes) -> Any:
        """Deserialize cached value"""
        try:
            # Try JSON first
            try:
                return json.loads(serialized_value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Fallback to pickle
                return pickle.loads(serialized_value)
        except Exception as e:
            logger.error(f"Error deserializing cache value: {e}")
            raise
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        stats = self.cache_stats.copy()
        
        # Calculate hit rate
        total_gets = stats['hits'] + stats['misses']
        stats['hit_rate'] = (stats['hits'] / total_gets * 100) if total_gets > 0 else 0
        
        # Add cache size info
        if self.redis_client:
            try:
                info = self.redis_client.info('memory')
                stats['memory_used'] = info.get('used_memory_human', 'Unknown')
                stats['cache_type'] = 'Redis'
            except:
                stats['memory_used'] = 'Unknown'
                stats['cache_type'] = 'Redis (error)'
        else:
            stats['memory_used'] = f"{len(self.memory_cache)} items"
            stats['cache_type'] = 'Memory'
        
        return stats
    
    def cleanup_expired(self):
        """Cleanup expired entries (for memory cache)"""
        if not self.redis_client:  # Redis handles expiry automatically
            current_time = datetime.utcnow()
            expired_keys = [
                key for key, data in self.memory_cache.items()
                if current_time > data['expiry']
            ]
            
            for key in expired_keys:
                del self.memory_cache[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def warm_cache(self):
        """Pre-populate cache with frequently accessed data"""
        logger.info("Warming up cache...")
        
        try:
            from .price_calculator import PriceCalculator
            calculator = PriceCalculator()
            
            # Cache category statistics
            category_stats = calculator.get_category_price_summary()
            if category_stats:
                self.cache_category_stats(category_stats)
            
            logger.info("Cache warm-up completed")
            
        except Exception as e:
            logger.error(f"Error during cache warm-up: {e}")
