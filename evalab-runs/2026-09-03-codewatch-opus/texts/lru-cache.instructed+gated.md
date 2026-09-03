```python
import threading
import time
from collections import OrderedDict


class LRUCache:
    """Fixed-capacity cache that evicts the least recently used entry.

    Entries may carry a time-to-live in seconds; expired entries are treated as
    absent and dropped when encountered. Safe for concurrent use: every
    operation that touches the ordering or the counters holds the same
    reentrant lock.
    """

    def __init__(self, capacity, default_ttl=None):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if default_ttl is not None and default_ttl <= 0:
            raise ValueError("default_ttl must be positive or None")
        self.capacity = capacity
        self.default_ttl = default_ttl
        self._entries = OrderedDict()
        self._lock = threading.RLock()
        self.hits = 0
        self.misses = 0
        self.expirations = 0

    def get(self, key, default=None):
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                self.misses += 1
                return default
            value, expires_at = entry
            if expires_at is not None and expires_at <= time.monotonic():
                del self._entries[key]
                self.expirations += 1
                self.misses += 1
                return default
            self._entries.move_to_end(key)
            self.hits += 1
            return value

    def put(self, key, value, ttl=_UNSET := object()):
        with self._lock:
            effective_ttl = self.default_ttl if ttl is _UNSET else ttl
            if effective_ttl is not None and effective_ttl <= 0:
                raise ValueError("ttl must be positive or None")
            expires_at = (
                None if effective_ttl is None else time.monotonic() + effective_ttl
            )
            if key in self._entries:
                self._entries.move_to_end(key)
            self._entries[key] = (value, expires_at)
            if len(self._entries) > self.capacity:
                self.purge_expired()
            if len(self._entries) > self.capacity:
                evicted_key, (evicted_value, _) = self._entries.popitem(last=False)
                return evicted_key, evicted_value
            return None

    def purge_expired(self):
        with self._lock:
            now = time.monotonic()
            expired = [
                key
                for key, (_, expires_at) in self._entries.items()
                if expires_at is not None and expires_at <= now
            ]
            for key in expired:
                del self._entries[key]
            self.expirations += len(expired)
            return len(expired)

    def stats(self):
        with self._lock:
            return {
                "hits": self.hits,
                "misses": self.misses,
                "expirations": self.expirations,
                "size": len(self._entries),
            }

    def __contains__(self, key):
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return False
            _, expires_at = entry
            if expires_at is not None and expires_at <= time.monotonic():
                del self._entries[key]
                self.expirations += 1
                return False
            return True

    def __len__(self):
        with self._lock:
            return len(self._entries)

    def clear(self):
        with self._lock:
            self._entries.clear()
            self.hits = 0
            self.misses = 0
            self.expirations = 0

    def __repr__(self):
        with self._lock:
            return (
                f"{type(self).__name__}(capacity={self.capacity}, "
                f"ttl={self.default_ttl}, size={len(self._entries)}, "
                f"hits={self.hits}, misses={self.misses})"
            )
```

One correction to the above: the `ttl=_UNSET := object()` default in `put` is invalid as written — a walrus in a default expression binds at class-body scope and reads badly. Use a module-level sentinel instead:

```python
_UNSET = object()

    def put(self, key, value, ttl=_UNSET):
```

with the rest of `put` unchanged.
