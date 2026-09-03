`put` now takes an optional `ttl` (seconds); expired entries are treated as misses on `get` and evicted lazily, and `__contains__` respects expiry too. Self-test passes.
