"""A least-recently-used cache backed by an OrderedDict."""

from collections import OrderedDict


class LRUCache:
    """Fixed-size mapping that evicts the least recently used entry.

    Both get and put count as uses, so they move a key to the
    most-recent end of the order. Eviction takes from the other end.
    """

    def __init__(self, max_size=128):
        if max_size <= 0:
            raise ValueError("max_size must be positive")
        self.max_size = max_size
        self._data = OrderedDict()

    def get(self, key, default=None):
        """Return the value for key, or default if it is absent."""
        if key not in self._data:
            return default
        self._data.move_to_end(key)
        return self._data[key]

    def put(self, key, value):
        """Store value under key, evicting the oldest entry if full."""
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        if len(self._data) > self.max_size:
            self._data.popitem(last=False)

    def __contains__(self, key):
        return key in self._data

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return f"LRUCache(max_size={self.max_size}, size={len(self._data)})"


if __name__ == "__main__":
    cache = LRUCache(max_size=2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.get("a")
    cache.put("c", 3)
    print(list(cache._data))  # ['a', 'c'] -- 'b' was the least recently used
