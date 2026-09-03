```python
import threading
import time
from collections import OrderedDict


class LRUCache:
    """Fixed-capacity cache that evicts the least recently used entry.

    An entry can carry a time-to-live. Once its deadline passes the entry
    is dead: lookups report a miss and drop it, and `purge_expired` clears
    the ones no lookup has touched.

    Safe for concurrent use: every method that reads or writes `_entries`
    holds `_lock`, so no two threads can interleave a lookup and a
    `move_to_end` and leave the recency order inconsistent.
    """

    _MISSING = object()

    def __init__(self, capacity, ttl=None, clock=time.monotonic):
        if capacity <= 0:
            raise ValueError(f"capacity must be positive, got {capacity}")
        if ttl is not None and ttl <= 0:
            raise ValueError(f"ttl must be positive or None, got {ttl}")
        self.capacity = capacity
        self.ttl = ttl
        self._clock = clock
        self._entries = OrderedDict()  # key -> (value, deadline or None)
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0
        self.expirations = 0

    def _deadline(self, ttl):
        """Absolute expiry time for an entry, or None if it never expires."""
        lifetime = self.ttl if ttl is self._MISSING else ttl
        if lifetime is None:
            return None
        if lifetime <= 0:
            raise ValueError(f"ttl must be positive or None, got {lifetime}")
        return self._clock() + lifetime

    def get(self, key, default=None):
        """Return the value for key and mark it most recently used."""
        with self._lock:
            entry = self._entries.get(key, self._MISSING)
            if entry is self._MISSING:
                self.misses += 1
                return default
            value, deadline = entry
            if deadline is not None and self._clock() >= deadline:
                del self._entries[key]
                self.expirations += 1
                self.misses += 1
                return default
            self._entries.move_to_end(key)
            self.hits += 1
            return value

    def put(self, key, value, ttl=_MISSING):
        """Store value under key, evicting the oldest entry if full.

        `ttl` overrides the cache-wide default for this entry; pass None for
        an entry that never expires. Returns the evicted (key, value) pair,
        or None if nothing was evicted.
        """
        with self._lock:
            entry = (value, self._deadline(ttl))
            if key in self._entries:
                self._entries[key] = entry
                self._entries.move_to_end(key)
                return None
            self._entries[key] = entry
            if len(self._entries) > self.capacity:
                evicted_key, (evicted_value, _) = self._entries.popitem(last=False)
                return evicted_key, evicted_value
            return None

    def purge_expired(self):
        """Drop every entry past its deadline and return how many went."""
        with self._lock:
            now = self._clock()
            dead = [
                key
                for key, (_, deadline) in self._entries.items()
                if deadline is not None and now >= deadline
            ]
            for key in dead:
                del self._entries[key]
            self.expirations += len(dead)
            return len(dead)

    def stats(self):
        """Return hit/miss/expiry counters and the current entry count."""
        with self._lock:
            return {
                "hits": self.hits,
                "misses": self.misses,
                "expirations": self.expirations,
                "size": len(self._entries),
            }

    def __contains__(self, key):
        with self._lock:
            entry = self._entries.get(key, self._MISSING)
            if entry is self._MISSING:
                return False
            _, deadline = entry
            return deadline is None or self._clock() < deadline

    def __len__(self):
        with self._lock:
            return len(self._entries)

    def __repr__(self):
        with self._lock:
            return (
                f"LRUCache(capacity={self.capacity}, ttl={self.ttl}, "
                f"size={len(self._entries)})"
            )
```

Expiry is lazy. A dead entry keeps its slot until a `get` lands on it or `purge_expired` runs, so it can still be the thing evicted when the cache overflows — which is the right choice, since it is the least useful entry to keep. If dead entries are holding memory you need back, call `purge_expired` from a sweeper thread; it is O(n) in the number of entries, so run it on a timer rather than per write.

`ttl` on `put` uses a sentinel default so the three cases stay distinct: omit it for the cache-wide default, pass a number for a per-entry lifetime, pass `None` for an entry that outlives every deadline.

The clock is injectable and defaults to `time.monotonic`, which does not jump when the system clock is adjusted. Tests can pass a counter and step it by hand instead of sleeping.

`size` in `stats()` counts entries still stored, including any that have expired but not yet been reaped, so it is an upper bound on what a lookup would find. `expirations` counts entries actually removed for age, whether by a lookup or by `purge_expired`, and does not overlap with capacity evictions.
