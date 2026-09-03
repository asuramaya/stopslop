`lru_cache.py` already exists in the working directory (untracked) and is exactly this: a 50-line `LRUCache` class over `OrderedDict` with `get`, `put`, a configurable `max_size`, plus `__contains__`, `__len__`, `__repr__` and a small demo block.

I ran it rather than rewriting it. Behavior checks out:

- `get` on a hit calls `move_to_end`, so reads count as uses — the eviction demo prints `['a', 'c']`, meaning `'b'` was correctly dropped.
- `put` on an existing key refreshes recency and overwrites the value (`('a', 9)` survived a later insert past capacity).
- `get` on a miss returns the `default` instead of raising.
- `max_size=0` raises `ValueError`.

One thing to flag: the class docstring says a use moves a key "to the front of the recency order", but the implementation moves it to the *end* of the OrderedDict and evicts with `popitem(last=False)`. The code is right; "front" in the docstring means front-of-queue in the informal sense and reads as contradicting the code. Say the word and I'll reword that line, or overwrite the file with a fresh implementation if you wanted a different design.
