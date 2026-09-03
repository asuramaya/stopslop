```python
import threading
import time
from collections import OrderedDict


class LRUCache:
    """Fixed-capacity cache that evicts the least recently used entry.

    Safe for concurrent use: every read is also a write (move_to_end plus a
    counter bump), so there is no read path that can skip the lock.

    Entries can carry a time-to-live in seconds, either as a cache-wide
    default or per put(). Expiry is lazy: a stale entry stays resident until
    someone asks for it, so len() and stats()["size"] count entries that may
    already be past their deadline.
    """

    def __init__(self, capacity, ttl=None):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if ttl is not None and ttl <= 0:
            raise ValueError("ttl must be positive or None")
        self.capacity = capacity
        self.ttl = ttl
        self._entries = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._expirations = 0

    def _expired(self, deadline, now):
        return deadline is not None and deadline <= now

    def get(self, key, default=None):
        now = time.monotonic()
        with self._lock:
            if key not in self._entries:
                self._misses += 1
                return default
            value, deadline = self._entries[key]
            if self._expired(deadline, now):
                del self._entries[key]
                self._expirations += 1
                self._misses += 1
                return default
            self._entries.move_to_end(key)
            self._hits += 1
            return value

    def put(self, key, value, ttl=None):
        if ttl is None:
            ttl = self.ttl
        elif ttl <= 0:
            raise ValueError("ttl must be positive or None")
        deadline = None if ttl is None else time.monotonic() + ttl
        with self._lock:
            if key in self._entries:
                self._entries.move_to_end(key)
            self._entries[key] = (value, deadline)
            if len(self._entries) > self.capacity:
                self._entries.popitem(last=False)

    def purge_expired(self):
        """Drop every entry past its deadline; returns how many were dropped."""
        now = time.monotonic()
        with self._lock:
            dead = [k for k, (_, d) in self._entries.items() if self._expired(d, now)]
            for key in dead:
                del self._entries[key]
            self._expirations += len(dead)
            return len(dead)

    def stats(self):
        with self._lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "expirations": self._expirations,
                "size": len(self._entries),
            }

    def __contains__(self, key):
        # membership must not count as a use, so no move_to_end here, and an
        # expired entry reads as absent without being charged as a miss
        now = time.monotonic()
        with self._lock:
            entry = self._entries.get(key)
            return entry is not None and not self._expired(entry[1], now)

    def __len__(self):
        with self._lock:
            return len(self._entries)

    def clear(self):
        with self._lock:
            self._entries.clear()
            self._hits = 0
            self._misses = 0
            self._expirations = 0

    def __repr__(self):
        s = self.stats()
        return "LRUCache(capacity={}, ttl={}, size={}, hits={}, misses={})".format(
            self.capacity, self.ttl, s["size"], s["hits"], s["misses"]
        )
```
