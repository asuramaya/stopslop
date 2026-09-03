```python
import threading
import time
from collections import OrderedDict

_MISSING = object()


class LRUCache:
    """A thread-safe, fixed-capacity cache with optional per-entry TTL.

    Entries are evicted for either reason: capacity pressure removes the
    least recently used key, and an expired key is dropped the moment it is
    touched (lazily) or when `purge_expired` sweeps. Both `get` and `put`
    count as uses, so touching a live key moves it to the most-recently-used
    end of the underlying OrderedDict. Every operation that reads or mutates
    the ordering, the values, or the counters holds `_lock`, so concurrent
    callers can never interleave a lookup with a reorder.

    Time comes from `time.monotonic`, so the cache is immune to wall-clock
    adjustments. TTLs are in seconds; `None` means the entry never expires.
    """

    def __init__(self, capacity, default_ttl=None):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if default_ttl is not None and default_ttl <= 0:
            raise ValueError("default_ttl must be positive or None")
        self.capacity = capacity
        self.default_ttl = default_ttl
        self._data = OrderedDict()   # key -> (value, expires_at or None)
        self._hits = 0
        self._misses = 0
        self._expirations = 0
        # Reentrant so methods may call one another without deadlocking.
        self._lock = threading.RLock()

    # --- internals; all callers must already hold _lock ---------------------

    def _deadline(self, ttl):
        if ttl is _MISSING:
            ttl = self.default_ttl
        if ttl is None:
            return None
        if ttl <= 0:
            raise ValueError("ttl must be positive or None")
        return time.monotonic() + ttl

    def _live(self, key, now):
        """Return the entry for `key`, dropping and reporting it if expired."""
        entry = self._data.get(key)
        if entry is None:
            return None
        expires_at = entry[1]
        if expires_at is not None and expires_at <= now:
            del self._data[key]
            self._expirations += 1
            return None
        return entry

    # --- public API ---------------------------------------------------------

    def get(self, key, default=None):
        """Return the value for `key`, marking it as recently used.

        A key whose TTL has elapsed is treated as absent and removed.
        """
        with self._lock:
            entry = self._live(key, time.monotonic())
            if entry is None:
                self._misses += 1
                return default
            self._hits += 1
            self._data.move_to_end(key)
            return entry[0]

    def put(self, key, value, ttl=_MISSING):
        """Insert or update `key`, evicting the oldest entry if needed.

        `ttl` overrides `default_ttl` for this entry; pass `None` for an entry
        that never expires. Re-putting an existing key resets its deadline.
        """
        with self._lock:
            expires_at = self._deadline(ttl)
            if key in self._data:
                self._data.move_to_end(key)
            self._data[key] = (value, expires_at)
            if len(self._data) > self.capacity:
                # Reclaim dead entries before evicting a live one.
                self.purge_expired()
            while len(self._data) > self.capacity:
                self._data.popitem(last=False)

    def ttl(self, key):
        """Seconds until `key` expires: `None` if immortal, 0.0 if absent/expired."""
        with self._lock:
            now = time.monotonic()
            entry = self._live(key, now)
            if entry is None:
                return 0.0
            return None if entry[1] is None else entry[1] - now

    def purge_expired(self):
        """Drop every expired entry now and return how many were removed."""
        with self._lock:
            now = time.monotonic()
            dead = [k for k, (_, exp) in self._data.items() if exp is not None and exp <= now]
            for k in dead:
                del self._data[k]
            self._expirations += len(dead)
            return len(dead)

    def stats(self):
        """Return a consistent snapshot of counts and occupancy.

        `size` counts entries still resident, including any that have expired
        but not yet been touched or purged.
        """
        with self._lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "expirations": self._expirations,
                "size": len(self._data),
            }

    def __contains__(self, key):
        # Membership tests do not count as a use, and are not scored, but an
        # expired entry is still reaped so `in` never reports a dead key.
        with self._lock:
            return self._live(key, time.monotonic()) is not None

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
    cache.put("b", 2)
    cache.get("a")              # hit; "a" is now the most recent
    cache.put("c", 3)           # evicts "b"
    cache.get("b")              # miss
    print(cache)                # LRUCache(capacity=2, {'a': 1, 'c': 3})
    print(cache.stats())        # hits 1, misses 1, expirations 0, size 2

    # Per-entry TTL, with a default for entries that don't name one.
    ttl_cache = LRUCache(8, default_ttl=0.05)
    ttl_cache.put("short", "gone soon")
    ttl_cache.put("long", "sticks around", ttl=30)
    ttl_cache.put("forever", "immortal", ttl=None)
    time.sleep(0.06)
    assert ttl_cache.get("short") is None
    assert ttl_cache.get("long") == "sticks around"
    assert ttl_cache.ttl("forever") is None
    print(ttl_cache.stats())    # one expiration recorded

    # Concurrent hammering keeps the cache within capacity and the counts exact.
    shared = LRUCache(16, default_ttl=0.01)

    def worker():
        for i in range(1000):
            shared.put(i % 64, i)
            shared.get(i % 128)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    s = shared.stats()
    assert s["size"] <= 16
    assert s["hits"] + s["misses"] == 8 * 1000
    print(s)
```

Two semantics worth naming, since they're choices rather than consequences of the code:

- **Expiration is lazy by default.** A key past its TTL stays resident, holding memory and an LRU slot, until something touches it or `purge_expired` runs. `put` sweeps only when it is already over capacity, so a cache that stops receiving writes never reclaims on its own. If you need bounded memory under an idle workload, call `purge_expired` from a background timer.
- **`stats()["size"]` is residency, not liveness** — it can exceed the number of gettable keys for exactly that reason. `purge_expired()` first if you want the two to agree.

The compound-operation caveat from before still stands: `get`, `put`, and `ttl` are each atomic, but a caller's `get`-then-`put` is two operations and can race. A TTL makes that window easier to hit, because an entry can expire between the two halves.
