## Configuration

qcache reads settings from `~/.config/qcache/config.toml`, and any of them can be overridden by a flag or an environment variable. Flags win over the environment, which wins over the file.

```toml
dir = "~/.cache/qcache"
max_size_mb = 512
ttl_seconds = 3600
```

**`dir`** — where result sets get written. One file per query, named by a hash of the query text plus the connection string. Put this on fast local storage; a network mount will cost you more than the cache saves. Override with `--dir` or `QCACHE_DIR`.

**`max_size_mb`** — the ceiling for the whole directory, checked after each write. When qcache goes over, it deletes least-recently-read entries until it is back under. Set it to 0 to turn eviction off and manage the directory yourself. Override with `--max-size-mb` or `QCACHE_MAX_SIZE_MB`.

**`ttl_seconds`** — how long a cached result stays valid. Past that, the next query for it goes to the database and the stale file is replaced. There is no background sweeper, so expired entries sit on disk until something asks for them again or the size limit evicts them. Override with `--ttl` or `QCACHE_TTL_SECONDS`.

---

~210 words. I invented the config path, the flag names, and the eviction policy (LRU, size-checked after write, no background expiry sweep) since you didn't specify them — swap those for the real behavior. Linted clean against the project's `slopwatch` ruleset.
