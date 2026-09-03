"""A fixed-capacity LRU cache built on OrderedDict."""

from collections import OrderedDict

_MISSING = object()


class LRUCache:
    """Maps keys to values, dropping the least recently used entry when full.

    Both get() and put() count as a use, so either one moves a key to the
    most-recent end of the order. Not thread-safe: a caller that shares one
    cache between threads has to do its own locking.
    """

    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._data = OrderedDict()

    def get(self, key, default=None):
        """Return the value for key, or default if key is absent."""
        value = self._data.get(key, _MISSING)
        if value is _MISSING:
            return default
        self._data.move_to_end(key)
        return value

    def put(self, key, value):
        """Store value under key, evicting the oldest entry if the cache is full."""
        if key in self._data:
            self._data[key] = value
            self._data.move_to_end(key)
            return
        if len(self._data) >= self.capacity:
            self._data.popitem(last=False)
        self._data[key] = value

    def __contains__(self, key):
        return key in self._data

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return "LRUCache(capacity={}, size={})".format(
            self.capacity, len(self._data))
