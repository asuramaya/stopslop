`lru_cache.py` now supports TTLs: `put(key, value, ttl=None)` per entry, plus a `LRUCache(capacity, default_ttl=None)` fallback.

- Values are stored as `(value, expires_at)`, with `expires_at` computed from `time.monotonic()` so a wall-clock adjustment cannot resurrect or prematurely kill an entry.
- Expiry is lazy — no timer thread. `_live()` checks one key and drops it on the spot; `_purge_expired()` sweeps the whole dict. Both assume the lock is held, so nothing new is exposed unlocked.
- `put` purges before evicting: if the cache is full but holds dead entries, those go first and a live LRU key survives. Only when every entry is live does it fall back to `popitem`.
- `len`, `in`, `stats` and `repr` all report live entries, so an expired key never inflates the size.
- `stats()` gained an `expired` counter. It sits apart from hits/misses — an expired lookup counts as a miss *and* an expiry, since those answer different questions ("did the caller get a value?" vs "was the TTL what cost them?").
- Re-putting a key resets its clock, and a bare `put` on a cache with a `default_ttl` inherits that TTL rather than becoming permanent.
- `ttl=None` means "no expiry" at the call site but "use the default" as the argument default; a non-positive `ttl` raises rather than storing something born dead.

Verified: the earlier no-TTL behaviour is byte-for-byte unchanged (`hits 1, misses 2, size 2`, `b` evicted); expiry, default vs per-call TTL, dead-entry reclamation ahead of eviction, and clock refresh all pass. Under 8 threads × 20k operations with a 10 ms default TTL, size stayed ≤ 16, `hits + misses` came to exactly 160,000, and no key duplicated in the ordering.

One caveat: `_purge_expired` is O(n) and `put` calls it on every insert once the cache is full. At capacity 16 that is free; at capacity 100k it is not. The usual fix is a second structure ordered by expiry (a heap of `(expires_at, key)`) so the sweep only touches entries that have actually died.
