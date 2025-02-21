from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import threading
from functools import lru_cache
from ..config import Config

class CacheManager:
    """Manages application-wide caching."""
    
    def __init__(self, config: Config):
        self.config = config
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        with self.lock:
            if key not in self.cache:
                return None
                
            entry = self.cache[key]
            if datetime.now() > entry['expires']:
                del self.cache[key]
                return None
                
            return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cache value with expiration."""
        if not self.config.get_cache_enable():
            return
            
        ttl = ttl or self.config.get_cache_max_age()
        expires = datetime.now() + timedelta(seconds=ttl)
        
        with self.lock:
            # Enforce cache size limit
            if len(self.cache) >= self.config.get_cache_max_size():
                self._evict_oldest()
                
            self.cache[key] = {
                'value': value,
                'expires': expires,
                'created': datetime.now()
            }
    
    def _evict_oldest(self) -> None:
        """Remove oldest cache entries."""
        with self.lock:
            if not self.cache:
                return
                
            oldest = min(self.cache.items(), key=lambda x: x[1]['created'])
            del self.cache[oldest[0]]
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear() 