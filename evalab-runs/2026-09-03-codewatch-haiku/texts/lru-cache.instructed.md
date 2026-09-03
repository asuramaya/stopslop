```python
from collections import OrderedDict
from threading import Lock
import time


class LRUCache:
    """A Least Recently Used cache backed by OrderedDict with optional per-entry TTL."""
    
    def __init__(self, capacity):
        """Initialize cache with maximum capacity."""
        self.capacity = capacity
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.lock = Lock()
    
    def get(self, key):
        """Retrieve value for key, marking it as recently used.
        
        Returns None if key not found or expired. Tracks hits and misses.
        """
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None
            value, expiry = self.cache[key]
            if expiry is not None and time.time() > expiry:
                del self.cache[key]
                self.misses += 1
                return None
            self.hits += 1
            self.cache.move_to_end(key)
            return value
    
    def put(self, key, value, ttl=None):
        """Store or update key-value pair with optional TTL in seconds.
        
        If the key exists, it is moved to the end (marked as recent).
        If cache exceeds capacity, the least recently used item is evicted.
        """
        with self.lock:
            expiry = None if ttl is None else time.time() + ttl
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = (value, expiry)
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)
    
    def stats(self):
        """Return cache statistics: hits, misses, and current size."""
        with self.lock:
            return {
                'hits': self.hits,
                'misses': self.misses,
                'size': len(self.cache)
            }
    
    def __len__(self):
        with self.lock:
            return len(self.cache)
    
    def __repr__(self):
        with self.lock:
            return f"LRUCache(capacity={self.capacity}, size={len(self.cache)})"
```
