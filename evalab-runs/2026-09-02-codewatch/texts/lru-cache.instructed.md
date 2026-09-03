```python
from collections import OrderedDict


class LRUCache:
    """Fixed-capacity cache that evicts the least recently used entry.

    Both `get` and `put` count as uses, so either one moves a key to the
    front of the eviction order.
    """

    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError(f"capacity must be at least 1, got {capacity}")
        self.capacity = capacity
        self._entries = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key, default=None):
        """Return the value for `key`, marking it as most recently used."""
        if key not in self._entries:
            self.misses += 1
            return default
        self.hits += 1
        self._entries.move_to_end(key, last=False)
        return self._entries[key]

    def put(self, key, value):
        """Store `value` under `key`, evicting the oldest entry if full.

        Returns the evicted (key, value) pair, or None if nothing was dropped.
        """
        if key in self._entries:
            self._entries[key] = value
            self._entries.move_to_end(key, last=False)
            return None

        evicted = None
        if len(self._entries) >= self.capacity:
            evicted = self._entries.popitem(last=True)
        self._entries[key] = value
        self._entries.move_to_end(key, last=False)
        return evicted

    def __len__(self):
        return len(self._entries)

    def __contains__(self, key):
        return key in self._entries
```
