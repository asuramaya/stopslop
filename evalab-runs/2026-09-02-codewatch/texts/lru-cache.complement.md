```python
from collections import OrderedDict


class LRUCache:
    """Fixed-size cache that evicts the least recently used entry."""

    _MISSING = object()

    def __init__(self, max_size=128):
        if max_size < 1:
            raise ValueError(f"max_size must be at least 1, got {max_size}")
        self.max_size = max_size
        self._entries = OrderedDict()

    def get(self, key, default=None):
        try:
            value = self._entries[key]
        except KeyError:
            return default
        self._entries.move_to_end(key)
        return value

    def put(self, key, value):
        self._entries[key] = value
        self._entries.move_to_end(key)
        if len(self._entries) > self.max_size:
            self._entries.popitem(last=False)

    def pop(self, key, default=_MISSING):
        if default is self._MISSING:
            return self._entries.pop(key)
        return self._entries.pop(key, default)

    def clear(self):
        self._entries.clear()

    def __contains__(self, key):
        return key in self._entries

    def __len__(self):
        return len(self._entries)

    def __iter__(self):
        """Iterate keys from least to most recently used."""
        return iter(self._entries)

    def __repr__(self):
        return f"{type(self).__name__}(max_size={self.max_size}, size={len(self._entries)})"
```
