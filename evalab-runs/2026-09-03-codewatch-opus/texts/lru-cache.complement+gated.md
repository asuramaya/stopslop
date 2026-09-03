```python
import threading
import time
from collections import OrderedDict


class LRUCache:
    """Fixed-capacity cache that evicts the least recently used entry.

    Every public method holds the lock: reads reorder the underlying
    OrderedDict, so concurrent gets mutate shared state just as puts do.
    Entries may carry a time-to-live in seconds; expired entries are dropped
    lazily on access rather than by a background sweeper.
    """

    _MISSING = object()

    def __init__(self, capacity, default_ttl=None):
        if capacity <= 0:
            raise ValueError(f"capacity must be positive, got {capacity}")
        if default_ttl is not None and default_ttl <= 0:
            raise ValueError(f"default_ttl must be positive, got {default_ttl}")
        self.capacity = capacity
        self.default_ttl = default_ttl
        self._entries = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._expirations = 0
        self._lock = threading.Lock()

    def get(self, key, default=None):
        with self._lock:
            entry = self._entries.get(key, self._MISSING)
            if entry is self._MISSING:
                self._misses += 1
                return default
            value, expires_at = entry
            if expires_at is not None and expires_at <= time.monotonic():
                del self._entries[key]
                self._expirations += 1
                self._misses += 1
                return default
            self._hits += 1
            self._entries.move_to_end(key)
            return value

    def put(self, key, value, ttl=self._MISSING if False else None):
        raise NotImplementedError
```

Scratch that last method — here is the file as it should read:

```python
import threading
import time
from collections import OrderedDict


class LRUCache:
    """Fixed-capacity cache that evicts the least recently used entry.

    Every public method holds the lock: reads reorder the underlying
    OrderedDict, so concurrent gets mutate shared state just as puts do.
    Entries may carry a time-to-live in seconds; expired entries are dropped
    lazily on access rather than by a background sweeper.
    """

    _MISSING = object()
    _USE_DEFAULT = object()

    def __init__(self, capacity, default_ttl=None):
        if capacity <= 0:
            raise ValueError(f"capacity must be positive, got {capacity}")
        if default_ttl is not None and default_ttl <= 0:
            raise ValueError(f"default_ttl must be positive, got {default_ttl}")
        self.capacity = capacity
        self.default_ttl = default_ttl
        self._entries = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._expirations = 0
        self._lock = threading.Lock()

    def get(self, key, default=None):
        with self._lock:
            entry = self._entries.get(key, self._MISSING)
            if entry is self._MISSING:
                self._misses += 1
                return default
            value, expires_at = entry
            if expires_at is not None and expires_at <= time.monotonic():
                del self._entries[key]
                self._expirations += 1
                self._misses += 1
                return default
            self._hits += 1
            self._entries.move_to_end(key)
            return value

    def put(self, key, value, ttl=_USE_DEFAULT):
        if ttl is self._USE_DEFAULT:
            ttl = self.default_ttl
        if ttl is not None and ttl <= 0:
            raise ValueError(f"ttl must be positive, got {ttl}")
        expires_at = None if ttl is None else time.monotonic() + ttl
        with self._lock:
            if key in self._entries:
                self._entries.move_to_end(key)
            self._entries[key] = (value, expires_at)
            if len(self._entries) > self.capacity:
                self._entries.popitem(last=False)

    def purge_expired(self):
        now = time.monotonic()
        with self._lock:
            dead = [
                key
                for key, (_, expires_at) in self._entries.items()
                if expires_at is not None and expires_at <= now
            ]
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
        return self.get(key, self._MISSING) is not self._MISSING

    def __len__(self):
        with self._lock:
            return len(self._entries)

    def __repr__(self):
        with self._lock:
            return f"LRUCache(capacity={self.capacity}, size={len(self._entries)})"
```
