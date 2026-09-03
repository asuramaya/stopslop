```python
from collections import OrderedDict
import threading
import time


class LRUCache:
    """Least Recently Used cache backed by OrderedDict with optional TTL."""

    def __init__(self, capacity):
        """Initialize cache with maximum capacity.

        Args:
            capacity: Maximum number of items to store.
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self.capacity = capacity
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.lock = threading.Lock()

    def get(self, key):
        """Retrieve value by key, marking it as recently used.

        Args:
            key: The key to look up.

        Returns:
            The cached value, or -1 if key not found or expired.
        """
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return -1
            
            value, timestamp, ttl = self.cache[key]
            if ttl is not None and time.time() - timestamp > ttl:
                del self.cache[key]
                self.misses += 1
                return -1
            
            self.hits += 1
            self.cache.move_to_end(key)
            return value

    def put(self, key, value, ttl=None):
        """Store key-value pair with optional TTL.

        Args:
            key: The key to store.
            value: The value to associate with key.
            ttl: Optional time-to-live in seconds.
        """
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = (value, time.time(), ttl)
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)

    def stats(self):
        """Return cache statistics.

        Returns:
            Dictionary with hits, misses, and current size.
        """
        with self.lock:
            return {
                'hits': self.hits,
                'misses': self.misses,
                'size': len(self.cache)
            }

    def __len__(self):
        """Return current number of cached items."""
        with self.lock:
            return len(self.cache)
```
