```python
import threading
import time
from collections import OrderedDict


class LRUCache:
    """Fixed-capacity cache that evicts the least recently used entry.

    Safe for concurrent use: every operation that reads or reorders `entries`
    holds `lock`, so two threads cannot interleave a lookup with the
    `move_to_end` that follows it.

    Entries can carry a time-to-live in seconds. Expired entries stay in
    `entries` until something touches them, so `size` counts entries that are
    expired but not yet reclaimed.
    """

    def __init__(self, capacity, ttl=None):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if ttl is not None and ttl <= 0:
            raise ValueError("ttl must be positive or None")
        self.capacity = capacity
        self.ttl = ttl
        self.entries = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.expirations = 0
        self.lock = threading.Lock()

    def get(self, key, default=None):
        now = time.monotonic()
        with self.lock:
            entry = self.entries.get(key)
            if entry is None:
                self.misses += 1
                return default

            value, expires_at = entry
            if expires_at is not None and expires_at <= now:
                del self.entries[key]
                self.expirations += 1
                self.misses += 1
                return default

            self.hits += 1
            self.entries.move_to_end(key)
            return value

    def put(self, key, value, ttl=None):
        """Store value under key, evicting the oldest entry if full.

        `ttl` overrides the cache-wide default for this entry; pass a number of
        seconds, or leave it unset to inherit. Returns the evicted
        (key, value) pair, or None if nothing was evicted.
        """
        lifetime = self.ttl if ttl is None else ttl
        if lifetime is not None and lifetime <= 0:
            raise ValueError("ttl must be positive or None")
        expires_at = None if lifetime is None else time.monotonic() + lifetime

        with self.lock:
            existed = key in self.entries
            self.entries[key] = (value, expires_at)
            if existed:
                self.entries.move_to_end(key)
                return None

            if len(self.entries) > self.capacity:
                evicted_key, (evicted_value, _) = self.entries.popitem(last=False)
                return evicted_key, evicted_value
            return None

    def purge_expired(self):
        """Drop every expired entry and return how many were removed.

        Expiry is otherwise lazy, so call this if the cache holds keys that are
        never read again and their values are large.
        """
        now = time.monotonic()
        with self.lock:
            dead = [
                key
                for key, (_, expires_at) in self.entries.items()
                if expires_at is not None and expires_at <= now
            ]
            for key in dead:
                del self.entries[key]
            self.expirations += len(dead)
            return len(dead)

    def stats(self):
        """Counts of lookups that hit and missed, plus the current entry count.

        A miss is counted for every `get` on an absent or expired key,
        including keys never written. `size` includes expired entries that no
        `get` or `purge_expired` has reclaimed yet.
        """
        with self.lock:
            return {
                "hits": self.hits,
                "misses": self.misses,
                "expirations": self.expirations,
                "size": len(self.entries),
            }

    def __contains__(self, key):
        with self.lock:
            entry = self.entries.get(key)
            if entry is None:
                return False
            expires_at = entry[1]
            return expires_at is None or expires_at > time.monotonic()

    def __len__(self):
        with self.lock:
            return len(self.entries)

    def __repr__(self):
        with self.lock:
            return f"LRUCache(capacity={self.capacity}, ttl={self.ttl}, size={len(self.entries)})"
```

`__contains__` reports expiry but does not remove the entry, so it stays cheap and lock-symmetric with `__len__`. Both remain unsafe as a guard before `get` — the key can expire or be evicted between the two calls; use `get` with a sentinel default.
