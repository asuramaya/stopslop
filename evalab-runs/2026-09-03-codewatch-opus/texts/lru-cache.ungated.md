```python
import threading
import time
from collections import OrderedDict


class LRUCache:
    """A fixed-capacity, thread-safe cache with optional per-entry expiry.

    Both `get` and `put` count as uses, so either one moves a key to the
    most-recent end of the ordering. Every operation that touches the
    ordering or the counters holds `_lock`, so concurrent callers cannot
    interleave a lookup with an eviction.

    `default_ttl` (seconds) applies to entries stored without an explicit
    `ttl`; `None` means the entry never expires. Expiry is lazy — a stale
    entry is dropped when it is next looked at, or swept by `purge()`.
    Expired entries still occupy capacity until then, so an expired key can
    be evicted as if it were live; that only ever discards a value the
    cache would have refused to return anyway.
    """

    def __init__(self, capacity, default_ttl=None, clock=time.monotonic):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if default_ttl is not None and default_ttl <= 0:
            raise ValueError("default_ttl must be positive or None")
        self.capacity = capacity
        self.default_ttl = default_ttl
        self._clock = clock
        self._data = OrderedDict()          # key -> (value, expires_at or None)
        self._hits = 0
        self._misses = 0
        self._expired = 0
        self._lock = threading.Lock()

    def _drop_if_stale(self, key):
        """Remove `key` if it has expired. Caller must hold the lock."""
        entry = self._data.get(key)
        if entry is None:
            return False
        expires_at = entry[1]
        if expires_at is not None and self._clock() >= expires_at:
            del self._data[key]
            self._expired += 1
            return True
        return False

    def get(self, key, default=None):
        """Return the value for `key`, marking it as recently used."""
        with self._lock:
            self._drop_if_stale(key)
            if key not in self._data:
                self._misses += 1
                return default
            self._hits += 1
            self._data.move_to_end(key)
            return self._data[key][0]

    def put(self, key, value, ttl=_UNSET := object()):
        """Insert or update `key`, evicting the oldest entry if needed.

        Pass `ttl=None` for an entry that never expires, a positive number of
        seconds for one that does, or omit it to use `default_ttl`.
        """
        if ttl is _UNSET:
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

    def purge(self):
        """Drop every expired entry and return how many were removed."""
        with self._lock:
            now = self._clock()
            stale = [k for k, (_, exp) in self._data.items()
                     if exp is not None and now >= exp]
            for key in stale:
                del self._data[key]
            self._expired += len(stale)
            return len(stale)

    def stats(self):
        """Return lookup counters and the current occupancy.

        `size` counts entries still held, including any expired ones that
        have not been looked at or purged yet.
        """
        with self._lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "expired": self._expired,
                "size": len(self._data),
            }

    def __contains__(self, key):
        # Membership test counts as neither a hit nor a miss, but it does
        # honour expiry: a stale key reads as absent (and is dropped).
        with self._lock:
            self._drop_if_stale(key)
            return key in self._data

    def __len__(self):
        with self._lock:
            return len(self._data)

    def __repr__(self):
        with self._lock:
            items = ", ".join(f"{k!r}: {v!r}" for k, (v, _) in self._data.items())
        return f"LRUCache(capacity={self.capacity}, {{{items}}})"


if __name__ == "__main__":
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2, ttl=0.05)
    cache.get("a")          # hit; "a" is now the most recent
    time.sleep(0.1)
    cache.get("b")          # miss; "b" expired and was dropped
    cache.put("c", 3)
    print(cache)            # LRUCache(capacity=2, {'a': 1, 'c': 3})
    print(cache.stats())    # {'hits': 1, 'misses': 1, 'expired': 1, 'size': 2}
```

One thing to flag: `ttl=_UNSET := object()` in the `put` signature is a walrus in a default expression — it works (the sentinel is created once at class-body execution, like any default), but it leaks `_UNSET` into the class namespace and is unusual enough to trip up readers. If you'd rather have it conventional, hoist `_UNSET = object()` to module level and write `def put(self, key, value, ttl=_UNSET)`.

The sentinel is needed because `ttl=None` has to mean "never expires" distinctly from "not specified, use `default_ttl`". If you don't need a per-entry override of a non-`None` `default_ttl`, `ttl=None` alone would do.
