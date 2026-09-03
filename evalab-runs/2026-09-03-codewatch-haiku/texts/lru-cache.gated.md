```python
from collections import OrderedDict
import threading
import time

class LRUCache:
    """A thread-safe LRU (Least Recently Used) cache with optional per-entry TTL."""
    
    def __init__(self, capacity: int):
        """Initialize the cache with a maximum capacity.
        
        Args:
            capacity: Maximum number of items to store in the cache.
        """
        self.capacity = capacity
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.lock = threading.Lock()
    
    def get(self, key: int) -> int:
        """Retrieve a value from the cache.
        
        Args:
            key: The key to look up.
            
        Returns:
            The value associated with the key, or -1 if not found or expired.
        """
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return -1
            
            value, expiry = self.cache[key]
            
            # Check if entry has expired
            if expiry is not None and time.time() > expiry:
                del self.cache[key]
                self.misses += 1
                return -1
            
            self.cache.move_to_end(key)
            self.hits += 1
            return value
    
    def put(self, key: int, value: int, ttl: float = None) -> None:
        """Store a key-value pair in the cache with optional TTL.
        
        Args:
            key: The key to store.
            value: The value to associate with the key.
            ttl: Optional time-to-live in seconds. None means no expiration.
        """
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            
            expiry = time.time() + ttl if ttl is not None else None
            self.cache[key] = (value, expiry)
            
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)
    
    def stats(self) -> dict:
        """Return cache statistics.
        
        Returns:
            A dictionary with 'hits', 'misses', and 'size'.
        """
        with self.lock:
            return {'hits': self.hits, 'misses': self.misses, 'size': len(self.cache)}
```
