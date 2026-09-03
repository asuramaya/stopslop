```python
import threading
import time
from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self._data = OrderedDict()
        self._expiry = {}
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
                del self._expiry[key]
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
            self._expiry[key] = time.monotonic() + ttl if ttl is not None else None
            if len(self._data) > self.capacity:
                oldest, _ = self._data.popitem(last=False)
                del self._expiry[oldest]

    def stats(self):
        with self._lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "size": len(self._data),
            }

    def _is_expired(self, key):
        deadline = self._expiry[key]
        return deadline is not None and time.monotonic() >= deadline
```
