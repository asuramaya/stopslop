```python
from collections import OrderedDict


class LRUCache:
    """A mapping that evicts the least recently used entry when full."""

    def __init__(self, max_size=128):
        if max_size <= 0:
            raise ValueError("max_size must be positive")
        self.max_size = max_size
        self._data = OrderedDict()

    def get(self, key, default=None):
        """Return the value for key and mark it most recently used."""
        if key not in self._data:
            return default
        self._data.move_to_end(key)
        return self._data[key]

    def put(self, key, value):
        """Store value under key, evicting the oldest entry if needed."""
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
    cache.get("a")          # "a" is now the newest
    cache.put("c", 3)       # evicts "b"
    print(cache.get("a"))   # 1
    print(cache.get("b"))   # None
    print(cache.get("c"))   # 3
```

Two details worth knowing:

- `__contains__` deliberately does not touch recency, so membership tests don't reorder the cache. If you want probing to count as a use, call `get` instead.
- `get` returns `default` on a miss, which is ambiguous if `None` is a legitimate stored value. If that matters for your data, use a sentinel object as the default and compare against it.

I kept this in the reply rather than writing a file, since you didn't name a destination — say the word and I'll drop it somewhere in the repo.
