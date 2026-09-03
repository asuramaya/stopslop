```python
from collections import OrderedDict


class LRUCache:
    """Fixed-size cache that evicts the least recently used entry.

    Both get and put count as a use, so a hot key stays resident even if it
    is never written again.
    """

    def __init__(self, max_size=128):
        if max_size < 1:
            raise ValueError(f"max_size must be at least 1, got {max_size}")
        self.max_size = max_size
        self._entries = OrderedDict()

    def get(self, key, default=None):
        if key not in self._entries:
            return default
        self._entries.move_to_end(key)
        return self._entries[key]

    def put(self, key, value):
        """Store value, returning the evicted (key, value) pair or None."""
        if key in self._entries:
            self._entries[key] = value
            self._entries.move_to_end(key)
            return None

        self._entries[key] = value
        if len(self._entries) > self.max_size:
            return self._entries.popitem(last=False)
        return None

    def discard(self, key):
        self._entries.pop(key, None)

    def clear(self):
        self._entries.clear()

    def __contains__(self, key):
        return key in self._entries

    def __len__(self):
        return len(self._entries)

    def __repr__(self):
        return f"LRUCache(max_size={self.max_size}, size={len(self._entries)})"
```
