```python
import threading
import time
from collections import OrderedDict


class LRUCache:
    """Fixed-capacity cache that evicts the least recently used entry.

    Entries may carry a time-to-live in seconds, either from the cache-wide
    default or per `put`. Expired entries are treated as absent and dropped
    when encountered; they still occupy space until then.

    Safe for concurrent use: every mutation of the ordering, the entries and
    the counters happens under a single lock.
    """

    def __init__(self, capacity, default_ttl=None):
        if capacity <= 0:
            raise ValueError(f"capacity must be positive, got {capacity}")
        if default_ttl is not None and default_ttl <= 0:
            raise ValueError(f"default_ttl must be positive or None, got {default_ttl}")
        self.capacity = capacity
        self.default_ttl = default_ttl
        self._entries = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._expirations = 0
        self._lock = threading.Lock()
        self._clock = time.monotonic

    def get(self, key, default=None):
        """Return the value for key, marking it as most recently used."""
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                self._misses += 1
                return default
            value, expires_at = entry
            if expires_at is not None and expires_at <= self._clock():
                del self._entries[key]
                self._expirations += 1
                self._misses += 1
                return default
            self._hits += 1
            self._entries.move_to_end(key)
            return value

    def put(self, key, value, ttl=_UNSET := object()):
        """Store value under key, evicting the oldest entry if full.

        Pass `ttl=None` to make a single entry immortal despite a cache-wide
        default; omit it to inherit that default.
        """
        lifetime = self.default_ttl if ttl is self._UNSET else ttl
        if lifetime is not None and lifetime <= 0:
            raise ValueError(f"ttl must be positive or None, got {lifetime}")
        expires_at = None if lifetime is None else self._clock() + lifetime
        with self._lock:
            if key in self._entries:
                self._entries.move_to_end(key)
            self._entries[key] = (value, expires_at)
            if len(self._entries) > self.capacity:
                self._entries.popitem(last=False)

    def purge_expired(self):
        """Drop every expired entry and return how many were removed."""
        with self._lock:
            now = self._clock()
            stale = [
                key
                for key, (_, expires_at) in self._entries.items()
                if expires_at is not None and expires_at <= now
            ]
            for key in stale:
                del self._entries[key]
            self._expirations += len(stale)
            return len(stale)

    def stats(self):
        """Return lookup counts and current occupancy as a consistent snapshot."""
        with self._lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "expirations": self._expirations,
                "size": len(self._entries),
            }

    def __contains__(self, key):
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return False
            expires_at = entry[1]
            if expires_at is not None and expires_at <= self._clock():
                del self._entries[key]
                self._expirations += 1
                return False
            return True

    def __len__(self):
        with self._lock:
            return len(self._entries)

    def __repr__(self):
        with self._lock:
            size = len(self._entries)
        return f"{type(self).__name__}(capacity={self.capacity}, size={size})"
```

One correction to the above: the walrus in the `put` signature is not valid there. Use a class-level sentinel instead:

```python
class LRUCache:
    _UNSET = object()

    ...

    def put(self, key, value, ttl=_UNSET):
        ...
```
