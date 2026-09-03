```python
import threading
import time
from collections import OrderedDict


class LRUCache:
    """Fixed-capacity cache that evicts the least recently used entry.

    Both get and put count as a use, so either one moves a key to the
    most-recent end of the ordering.

    An entry can carry a time-to-live in seconds. Expiry is lazy: a stale
    entry stays in the ordering until something touches it, so a key that
    is never read again is reclaimed by eviction rather than by its TTL.
    Call purge_expired() if you need the size to reflect live entries only.

    Safe to share between threads: every method holds a lock for the whole
    read-modify-write, so no thread can observe or extend a half-updated
    ordering. The lock is reentrant only to keep nesting cheap if a method
    grows to call another one.
    """

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
        self._expired = 0
        self._lock = threading.RLock()

    def _now(self):
        # Monotonic, so a wall-clock jump cannot resurrect or kill an entry.
        return time.monotonic()

    def _deadline(self, ttl):
        if ttl is None:
            ttl = self.default_ttl
        if ttl is None:
            return None
        if ttl <= 0:
            raise ValueError(f"ttl must be positive, got {ttl}")
        return self._now() + ttl

    def get(self, key, default=None):
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                self._misses += 1
                return default

            value, deadline = entry
            if deadline is not None and deadline <= self._now():
                del self._entries[key]
                self._expired += 1
                self._misses += 1
                return default

            self._hits += 1
            self._entries.move_to_end(key)
            return value

    def put(self, key, value, ttl=None):
        """Store value under key, evicting the oldest entry if full.

        ttl overrides default_ttl for this entry; pass a positive number of
        seconds, or leave it None to inherit. There is no way to give one
        entry an unlimited lifetime when default_ttl is set.

        Returns the evicted (key, value) pair, or None if nothing was
        evicted, so callers can flush the entry to a backing store. Flush
        outside this call: the lock is released by the time you get the pair.
        """
        deadline = self._deadline(ttl)
        with self._lock:
            if key in self._entries:
                self._entries[key] = (value, deadline)
                self._entries.move_to_end(key)
                return None

            self._entries[key] = (value, deadline)
            if len(self._entries) > self.capacity:
                # Prefer dropping something already dead over a live entry.
                self._drop_one_expired()
            if len(self._entries) > self.capacity:
                evicted_key, (evicted_value, _) = self._entries.popitem(last=False)
                return evicted_key, evicted_value
            return None

    def _drop_one_expired(self):
        """Remove the least recent expired entry, if there is one.

        Caller holds the lock. Scans from the least-recent end and stops at
        the first live entry it finds, so the cost is bounded by the number
        of dead entries it actually reclaims.
        """
        now = self._now()
        for key, (_, deadline) in list(self._entries.items()):
            if deadline is None or deadline > now:
                continue
            del self._entries[key]
            self._expired += 1
            return

    def purge_expired(self):
        """Drop every expired entry and return how many went."""
        with self._lock:
            now = self._now()
            dead = [
                key
                for key, (_, deadline) in self._entries.items()
                if deadline is not None and deadline <= now
            ]
            for key in dead:
                del self._entries[key]
            self._expired += len(dead)
            return len(dead)

    def stats(self):
        """Counts since construction; clear() does not reset them.

        size counts entries still held, including any that have expired but
        have not been touched yet.
        """
        with self._lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "expired": self._expired,
                "size": len(self._entries),
            }

    def __contains__(self, key):
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return False
            deadline = entry[1]
            if deadline is not None and deadline <= self._now():
                del self._entries[key]
                self._expired += 1
                return False
            return True

    def __len__(self):
        with self._lock:
            return len(self._entries)

    def keys(self):
        """Live keys from least to most recently used, copied under the lock."""
        with self._lock:
            now = self._now()
            return [
                key
                for key, (_, deadline) in self._entries.items()
                if deadline is None or deadline > now
            ]

    def clear(self):
        with self._lock:
            self._entries.clear()
```

Two things worth knowing. `__contains__` counts an expiry against the `expired` stat but not against hits or misses, so a membership test does not distort the hit rate. And `__len__` still reports stored entries rather than live ones — making it filter would mean an O(n) scan on every `len()`, which is the wrong trade for a method people call in loops; `keys()` and `purge_expired()` are the honest views.
