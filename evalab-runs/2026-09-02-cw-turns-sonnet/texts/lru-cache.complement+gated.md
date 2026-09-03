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
        self._expires = {}
        self._hits = 0
        self._misses = 0
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            if key not in self._data:
                self._misses += 1
                return None
            if self._is_expired(key):
                del self._data[key]
                del self._expires[key]
                self._misses += 1
                return None
            self._hits += 1
            self._data.move_to_end(key)
            return self._data[key]

    def put(self, key, value, ttl=None):
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
            self._data[key] = value
            self._expires[key] = time.monotonic() + ttl if ttl is not None else None
            if len(self._data) > self.capacity:
                oldest, _ = self._data.popitem(last=False)
                del self._expires[oldest]

    def _is_expired(self, key):
        expires_at = self._expires[key]
        return expires_at is not None and time.monotonic() >= expires_at

    def stats(self):
        with self._lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "size": len(self._data),
            }

    def __len__(self):
        with self._lock:
            return len(self._data)

    def __contains__(self, key):
        with self._lock:
            return key in self._data and not self._is_expired(key)
```
