`lru.py:23` — TTL added, 120 lines, checks pass (single-thread TTL cases plus the 8-thread hammer: size stayed ≤ 50, hits + misses matched the get count exactly).

What changed:

- Values are now `(value, expires_at)` pairs. `expires_at` is `time.monotonic()`-based, so a wall-clock change cannot resurrect or kill an entry early.
- `put(key, value, ttl=None)` takes a per-entry lifetime in seconds; `LRUCache(capacity, default_ttl=...)` sets the fallback. `ttl=None` on a cache without a default means no expiry, same as before.
- Expiry is lazy, matching `lru_cache.py`: `get` and `__contains__` drop a single dead entry through `_live`, and `stats`/`__len__`/`__repr__` sweep with `_purge_expired` so the size they report only counts live entries.
- `put` sweeps expired entries before it evicts, so a dead entry is reclaimed in preference to a live LRU one. The `popitem(last=False)` only runs if the sweep freed nothing.
- `stats()` gained an `"expired"` key, so it is now the same four names `lru_cache.py` returns.

Two behaviours worth naming, both inherited from `lru_cache.py`:

- Reading an expired entry counts as a miss *and* an expiration, so `hits + misses` still equals the number of `get` calls, but `expired` overlaps with `misses` rather than adding to it.
- Overwriting an existing key resets its clock: `put` recomputes `expires_at` even on the update path. There is no way to change a value and keep the old deadline.

`capacity` counts stored entries, not live ones, in the window between a key expiring and something looking at it. A cache full of dead entries still refuses nothing, since `put` sweeps first, but `len()` and `stats()["size"]` are the honest numbers.
