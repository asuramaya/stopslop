```python
import threading
import time
from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._data = OrderedDict()
        self._expires_at = {}
        self._hits = 0
        self._misses = 0
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            if key not in self._data:
                self._misses += 1
                return None
            expires_at = self._expires_at.get(key)
            if expires_at is not None and expires_at <= time.monotonic():
                del self._data[key]
                del self._expires_at[key]
                self._misses += 1
                return None
            self._data.move_to_end(key)
            self._hits += 1
            return self._data[key]

    def put(self, key, value, ttl=None):
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
            self._data[key] = value
            if ttl is None:
                self._expires_at.pop(key, None)
            else:
                self._expires_at[key] = time.monotonic() + ttl
            if len(self._data) > self.capacity:
                oldest_key, _ = self._data.popitem(last=False)
                self._expires_at.pop(oldest_key, None)

    def stats(self):
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total else 0.0
            return {
                "hits": self._hits,
                "misses": self._misses,
                "size": len(self._data),
                "hit_rate": hit_rate,
            }

    def __len__(self):
        with self._lock:
            return len(self._data)

    def __contains__(self, key):
        with self._lock:
            return key in self._data
```
