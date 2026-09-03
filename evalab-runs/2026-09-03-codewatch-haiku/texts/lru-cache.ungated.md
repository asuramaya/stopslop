```python
from collections import OrderedDict
import threading
import time

class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.lock = threading.Lock()
    
    def get(self, key):
        """Get value and mark as most recently used."""
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return -1
            
            value, ttl, timestamp = self.cache[key]
            
            # Check if entry has expired
            if ttl is not None and time.time() - timestamp > ttl:
                del self.cache[key]
                self.misses += 1
                return -1
            
            # Move to end to mark as recently used
            self.cache.move_to_end(key)
            self.hits += 1
            return value
    
    def put(self, key, value, ttl=None):
        """Put key-value pair with optional TTL, evicting LRU item if necessary."""
        with self.lock:
            if key in self.cache:
                # Update existing key
                self.cache[key] = (value, ttl, time.time())
                self.cache.move_to_end(key)
            else:
                # Add new key
                self.cache[key] = (value, ttl, time.time())
                # Evict least recently used if over capacity
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


# Example usage:
if __name__ == "__main__":
    lru = LRUCache(capacity=2)
    
    lru.put(1, "a", ttl=1.0)
    lru.put(2, "b")
    print(lru.get(1))          # 'a'
    
    lru.put(3, "c")            # Evicts 2
    print(lru.get(2))          # -1 (evicted)
    
    time.sleep(1.1)
    print(lru.get(1))          # -1 (expired)
    
    lru.put(4, "d")
    print(lru.get(4))          # 'd'
    
    print(lru.stats())
```
