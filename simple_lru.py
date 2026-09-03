import threading
import time
from collections import OrderedDict


class LRUCache:
    """Fixed-capacity cache that evicts the least recently used key."""

    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._data = OrderedDict()
        self._expires_at = {}
        self._hits = 0
        self._misses = 0
        self._lock = threading.Lock()

    def get(self, key, default=None):
        with self._lock:
            if key not in self._data or self._is_expired(key):
                self._data.pop(key, None)
                self._expires_at.pop(key, None)
                self._misses += 1
                return default
            self._hits += 1
            self._data.move_to_end(key)
            return self._data[key]

    def put(self, key, value, ttl=None):
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
            self._data[key] = value
            if ttl is None:
                self._expires_at.pop(key, None)
            else:
                self._expires_at[key] = time.monotonic() + ttl
            if len(self._data) > self.capacity:
                oldest, _ = self._data.popitem(last=False)
                self._expires_at.pop(oldest, None)

    def _is_expired(self, key):
        expires_at = self._expires_at.get(key)
        return expires_at is not None and time.monotonic() >= expires_at

    def stats(self):
        with self._lock:
            return {"hits": self._hits, "misses": self._misses, "size": len(self._data)}

    def __len__(self):
        with self._lock:
            return len(self._data)

    def __contains__(self, key):
        with self._lock:
            return key in self._data and not self._is_expired(key)


if __name__ == "__main__":
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.get("a")
    cache.put("c", 3)
    assert "b" not in cache
    assert cache.get("a") == 1
    assert cache.get("c") == 3
    assert cache.stats() == {"hits": 3, "misses": 0, "size": 2}

    ttl_cache = LRUCache(2)
    ttl_cache.put("x", 1, ttl=0.01)
    assert ttl_cache.get("x") == 1
    time.sleep(0.02)
    assert ttl_cache.get("x") is None
    assert "x" not in ttl_cache

    print("ok")
