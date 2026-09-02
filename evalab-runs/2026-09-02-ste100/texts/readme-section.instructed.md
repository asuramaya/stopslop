## Configuration

qcache reads its settings from `~/.config/qcache/config.toml`. Command-line flags override the file. Three settings control the cache.

`cache_dir` sets where qcache writes result files. The default is `~/.cache/qcache`. Point it at a fast local disk, not a network mount. If the directory does not exist, qcache creates it on first run.

`max_size_mb` caps total disk use, in megabytes. The default is 512. When a write pushes the cache past the cap, qcache evicts the least recently read entries until the total fits again. A value of 0 disables the cap. Note that qcache checks the cap after each write, so the cache can briefly exceed it by the size of one result.

`ttl_seconds` sets how long a cached result stays valid. The default is 3600. After that many seconds, qcache treats the entry as a miss and runs the query again. Set a short TTL for tables that change often. Set a long one for reporting snapshots that you rebuild nightly.

```toml
cache_dir = "/var/lib/qcache"
max_size_mb = 2048
ttl_seconds = 900
```

Equivalent flags: `--cache-dir`, `--max-size-mb`, `--ttl-seconds`. Run `qcache config show` to print the settings that qcache resolved for the current invocation.
