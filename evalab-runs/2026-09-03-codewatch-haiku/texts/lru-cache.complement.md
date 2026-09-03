```python
import time
from collections import OrderedDict
from threading import Lock


class LRUCache:
    """Least Recently Used cache with O(1) get and put operations."""
    
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.lock = Lock()
    
    def get(self, key):
        """Return value if key exists and not expired, else None. Mark accessed keys as recently used."""
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None
            value, expiry_time = self.cache[key]
            if expiry_time is not None and time.time() > expiry_time:
                del self.cache[key]
                self.misses += 1
                return None
            self.hits += 1
            self.cache.move_to_end(key)
            return value
    
    def put(self, key, value, ttl=None):
        """Add or update key-value pair with optional time-to-live. Evict least recently used item if over capacity."""
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            expiry_time = time.time() + ttl if ttl is not None else None
            self.cache[key] = (value, expiry_time)
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
```
