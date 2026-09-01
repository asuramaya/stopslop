## Configuration

qcache reads settings from `~/.config/qcache/config.toml`. Values there can be overridden by an environment variable, and an environment variable can be overridden by a command-line flag.

```toml
cache_dir    = "~/.cache/qcache"
max_size_mb  = 512
ttl_seconds  = 3600
```

**`cache_dir`** is where result files are written. The directory is created on first run if it doesn't exist. Point it at a local disk; qcache writes and renames files often, and network mounts make that slow. Override with `QCACHE_DIR` or `--cache-dir`.

**`max_size_mb`** is the ceiling on total cache size. When a new result would push the cache past it, qcache deletes the least recently read entries until there is room. A single result larger than the ceiling is never cached at all. Override with `QCACHE_MAX_SIZE_MB` or `--max-size-mb`.

**`ttl_seconds`** is how long a cached result stays valid. Past that age an entry counts as a miss and the query runs against the database again. Set it to `0` to turn expiry off and rely on the size limit alone. Override with `QCACHE_TTL` or `--ttl`.

Run `qcache config` to print the settings currently in effect, along with where each one came from.
