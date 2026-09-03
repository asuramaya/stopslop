```python
from collections import OrderedDict


class LRUCache:
    """Fixed-capacity cache that evicts the least recently used entry.

    Both get and put count as uses, so either one moves a key to the
    most-recent end of the ordering.
    """

    def __init__(self, capacity=128):
        if capacity < 1:
            raise ValueError(f"capacity must be at least 1, got {capacity}")
        self.capacity = capacity
        self._entries = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key, default=None):
        if key not in self._entries:
            self.misses += 1
            return default
        self._entries.move_to_end(key)
        self.hits += 1
        return self._entries[key]

    def put(self, key, value):
        """Store value under key, evicting the oldest entry if full.

        Returns the evicted (key, value) pair, or None if nothing was
        evicted.
        """
        if key in self._entries:
            self._entries[key] = value
            self._entries.move_to_end(key)
            return None
        self._entries[key] = value
        if len(self._entries) > self.capacity:
            return self._entries.popitem(last=False)
        return None

    def __contains__(self, key):
        return key in self._entries

    def __len__(self):
        return len(self._entries)

    def clear(self):
        self._entries.clear()
        self.hits = 0
        self.misses = 0
```
