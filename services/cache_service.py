import json
import time
from typing import Optional, Any

class DistributedCacheService:
    """Simulated distributed cache"""
    
    def __init__(self):
        self.cache = {}
        self.ttl_cache = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            if key in self.ttl_cache and time.time() > self.ttl_cache[key]:
                del self.cache[key]
                del self.ttl_cache[key]
                return None
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        self.cache[key] = value
        self.ttl_cache[key] = time.time() + ttl
    
    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]
        if key in self.ttl_cache:
            del self.ttl_cache[key]
    
    def get_stats(self):
        return {
            "total_keys": len(self.cache),
            "hit_rate": 0.85,  # Mock
            "memory_usage": "45MB"  # Mock
        }

cache_service = DistributedCacheService()