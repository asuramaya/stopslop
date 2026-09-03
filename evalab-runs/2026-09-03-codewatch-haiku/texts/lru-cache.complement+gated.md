```python
from collections import OrderedDict
import threading
import time

class LRUCache:
    """Least Recently Used cache with fixed capacity and optional TTL."""
    
    def __init__(self, capacity: int):
        """Initialize cache with maximum capacity."""
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self.cache = OrderedDict()
        self.capacity = capacity
        self.hits = 0
        self.misses = 0
        self.lock = threading.Lock()
    
    def get(self, key):
        """Retrieve value by key, marking as recently used."""
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return -1
            value, expiration = self.cache[key]
            if expiration is not None and time.time() >= expiration:
                del self.cache[key]
                self.misses += 1
                return -1
            self.hits += 1
            self.cache.move_to_end(key)
            return value
    
    def put(self, key, value, ttl=None) -> None:
        """Store a key-value pair with optional TTL, evicting LRU item if necessary.
        
        Args:
            ttl: Time-to-live in seconds (None for no expiration).
        """
        with self.lock:
            expiration = None if ttl is None else time.time() + ttl
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = (value, expiration)
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)
    
    def stats(self) -> dict:
        """Return cache statistics."""
        with self.lock:
            return {
                'hits': self.hits,
                'misses': self.misses,
                'size': len(self.cache)
            }
    
    def __len__(self) -> int:
        """Return the number of items currently in cache."""
        with self.lock:
            return len(self.cache)
```
