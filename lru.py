"""A fixed-capacity LRU cache built on OrderedDict."""

import threading
import time
from collections import OrderedDict


class LRUCache:
    """Maps keys to values, dropping the least recently used entry when full.

    Both get() and put() count as a use, so either one moves a key to the
    most-recent end of the order.

    An entry can carry a time-to-live in seconds, after which it reads as
    absent. Expiry is lazy: an entry goes away when something looks at it,
    not on a timer.

    Every method holds a lock for the whole read-modify-write, so the cache
    is safe to share between threads.
    """

    def __init__(self, capacity, default_ttl=None):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if default_ttl is not None and default_ttl <= 0:
            raise ValueError("default_ttl must be positive or None")
        self.capacity = capacity
        self.default_ttl = default_ttl
        self._data = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._expirations = 0

    def get(self, key, default=None):
        """Return the value for key, or default if it is absent or expired."""
        with self._lock:
            if not self._live(key):
                self._misses += 1
                return default
            self._hits += 1
            self._data.move_to_end(key)
            return self._data[key][0]

    def put(self, key, value, ttl=None):
        """Store value under key, evicting the oldest entry if needed.

        ttl is a lifetime in seconds; None falls back to default_ttl, and a
        cache built without one keeps the entry until eviction.
        """
        if ttl is None:
            ttl = self.default_ttl
        elif ttl <= 0:
            raise ValueError("ttl must be positive or None")
        expires_at = None if ttl is None else time.monotonic() + ttl
        with self._lock:
            if key in self._data:
                self._data[key] = (value, expires_at)
                self._data.move_to_end(key)
                return
            if len(self._data) >= self.capacity:
                self._purge_expired()
            if len(self._data) >= self.capacity:
                self._data.popitem(last=False)
            self._data[key] = (value, expires_at)

    def stats(self):
        """Return get() hit and miss counts, expirations, and entry count.

        Only get() moves hits and misses; `in` and put() leave them alone.
        size counts live entries, so an expired entry still in _data is not
        included.
        """
        with self._lock:
            self._purge_expired()
            return {
                "hits": self._hits,
                "misses": self._misses,
                "expired": self._expirations,
                "size": len(self._data),
            }

    def _live(self, key):
        """True if key is present and unexpired; drops it if it has expired.

        Callers must hold the lock.
        """
        entry = self._data.get(key)
        if entry is None:
            return False
        expires_at = entry[1]
        if expires_at is not None and expires_at <= time.monotonic():
            del self._data[key]
            self._expirations += 1
            return False
        return True

    def _purge_expired(self):
        """Drop every expired entry. Callers must hold the lock."""
        now = time.monotonic()
        dead = [k for k, (_, exp) in self._data.items()
                if exp is not None and exp <= now]
        for key in dead:
            del self._data[key]
        self._expirations += len(dead)

    def __contains__(self, key):
        with self._lock:
            return self._live(key)

    def __len__(self):
        with self._lock:
            self._purge_expired()
            return len(self._data)

    def __repr__(self):
        with self._lock:
            self._purge_expired()
            size = len(self._data)
        return "LRUCache(capacity={}, size={})".format(self.capacity, size)
