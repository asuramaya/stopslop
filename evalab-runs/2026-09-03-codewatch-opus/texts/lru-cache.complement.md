```python
import threading
import time
from collections import OrderedDict


class LRUCache:
    """Fixed-capacity cache that evicts the least recently used entry.

    Entries may carry a time-to-live in seconds, either per-key or from a
    default set on the cache. Expired entries are dropped lazily on access;
    they still occupy capacity until then, so an expired key can be the one
    evicted to make room, which is the outcome we want anyway.

    Safe for concurrent use: every operation that touches the ordering or the
    counters holds the lock, so a reader's move_to_end cannot interleave with
    another thread's eviction.
    """

    def __init__(self, capacity, default_ttl=None):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if default_ttl is not None and default_ttl <= 0:
            raise ValueError("default_ttl must be positive or None")
        self.capacity = capacity
        self.default_ttl = default_ttl
        self._data = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._expirations = 0
        self._lock = threading.Lock()
        # Monotonic: wall-clock jumps must not resurrect or prematurely kill entries.
        self._clock = time.monotonic

    def _expired(self, expires_at, now):
        return expires_at is not None and expires_at <= now

    def get(self, key, default=None):
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                self._misses += 1
                return default
            value, expires_at = entry
            if self._expired(expires_at, self._clock()):
                del self._data[key]
                self._expirations += 1
                self._misses += 1
                return default
            self._hits += 1
            self._data.move_to_end(key)
            return value

    def put(self, key, value, ttl=None):
        if ttl is None:
            ttl = self.default_ttl
        if ttl is not None and ttl <= 0:
            raise ValueError("ttl must be positive or None")
        expires_at = None if ttl is None else self._clock() + ttl
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
            self._data[key] = (value, expires_at)
            if len(self._data) > self.capacity:
                self._data.popitem(last=False)

    def purge_expired(self):
        with self._lock:
            now = self._clock()
            dead = [k for k, (_, exp) in self._data.items() if self._expired(exp, now)]
            for key in dead:
                del self._data[key]
            self._expirations += len(dead)
            return len(dead)

    def stats(self):
        with self._lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "expirations": self._expirations,
                "size": len(self._data),
            }

    def pop(self, key, default=None):
        with self._lock:
            entry = self._data.pop(key, None)
            if entry is None:
                return default
            value, expires_at = entry
            if self._expired(expires_at, self._clock()):
                self._expirations += 1
                return default
            return value

    def clear(self):
        with self._lock:
            self._data.clear()
            self._hits = 0
            self._misses = 0
            self._expirations = 0

    def __contains__(self, key):
        with self._lock:
            entry = self._data.get(key)
            return entry is not None and not self._expired(entry[1], self._clock())

    def __len__(self):
        # Counts entries still held, including any that have expired unnoticed.
        with self._lock:
            return len(self._data)

    def __iter__(self):
        # Snapshot under the lock: iterating the live OrderedDict would raise if
        # another thread inserted or evicted mid-iteration. Oldest first.
        with self._lock:
            now = self._clock()
            live = [k for k, (_, exp) in self._data.items() if not self._expired(exp, now)]
        return iter(live)

    def __repr__(self):
        with self._lock:
            return f"LRUCache(capacity={self.capacity}, size={len(self._data)})"
```
