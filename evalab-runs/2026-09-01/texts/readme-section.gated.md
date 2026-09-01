## Configuration

qcache reads `~/.config/qcache/config.toml` if it exists. Every key there also has an environment variable and a command-line flag; flags beat environment variables, which beat the file.

```toml
cache_dir   = "~/.cache/qcache"
max_size_mb = 512
ttl_seconds = 3600
```

**`cache_dir`** (`QCACHE_DIR`, `--cache-dir`)
Where result files are written, `~/.cache/qcache` unless you say otherwise. qcache creates the directory on first run. Keep it on a local disk; pointing it at an NFS mount usually costs more than the queries you are trying to avoid.

**`max_size_mb`** (`QCACHE_MAX_SIZE_MB`, `--max-size-mb`)
Ceiling on total cache size, 512 out of the box. When a new result would push the directory past the limit, qcache drops least-recently-read entries until it fits again. A single result bigger than the whole limit is never cached.

**`ttl_seconds`** (`QCACHE_TTL`, `--ttl`)
How long a cached result counts as fresh, an hour if you leave it alone. Once an entry expires, the next matching query goes back to the database and overwrites it. Set this to 0 to turn expiry off and let size eviction do all the work.

Expiry is checked on read, so stale entries occupy disk until something asks for them or eviction sweeps them out.
