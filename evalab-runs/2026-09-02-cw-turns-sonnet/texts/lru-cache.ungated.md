```python
import threading
import time
from collections import OrderedDict


class LRUCache:
    """Fixed-capacity cache that evicts the least recently used entry."""

    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._data = OrderedDict()
        self._expires = {}
        self._hits = 0
        self._misses = 0
        self._lock = threading.Lock()

    def get(self, key, default=None):
        with self._lock:
            if key not in self._data or self._is_expired(key):
                self._data.pop(key, None)
                self._expires.pop(key, None)
                self._misses += 1
                return default
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
                self._expires.pop(oldest, None)

    def _is_expired(self, key):
        deadline = self._expires.get(key)
        return deadline is not None and time.monotonic() >= deadline

    def stats(self):
        with self._lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "size": len(self._data),
            }

    def __contains__(self, key):
        with self._lock:
            return key in self._data and not self._is_expired(key)

    def __len__(self):
        with self._lock:
            return len(self._data)

    def __repr__(self):
        return "LRUCache(capacity={}, size={})".format(
            self.capacity, len(self._data)
        )
```

`ttl` is optional and per-entry: `put(key, value, ttl=30)` sets a 30-second deadline in `_expires`, stored as `time.monotonic()` so it's immune to wall-clock changes; `put` without `ttl` stores `None`, meaning no expiry. `get` and `__contains__` check `_is_expired` and treat an expired entry as absent, evicting it from both dicts on the way out. Expired entries that are never `get`-checked still sit in memory until evicted by capacity — there's no background sweeper, which is a reasonable tradeoff at this size but worth knowing if TTLs are short and entries are rarely read.

Still standalone, not written to any file in the repo.
