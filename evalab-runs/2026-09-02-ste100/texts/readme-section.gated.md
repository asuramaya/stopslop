## Configuration

qcache reads settings from three places. Lowest priority is the config file at `~/.config/qcache/config.toml`, then environment variables, then command-line flags. A flag always wins.

| Option | File key | Environment variable | Flag | Default |
| --- | --- | --- | --- | --- |
| Cache directory | `dir` | `QCACHE_DIR` | `--dir` | `~/.cache/qcache` |
| Maximum size | `max_size_mb` | `QCACHE_MAX_SIZE_MB` | `--max-size-mb` | `512` |
| Time to live | `ttl_seconds` | `QCACHE_TTL` | `--ttl` | `3600` |

A minimal config file:

```toml
dir = "/var/lib/qcache"
max_size_mb = 2048
ttl_seconds = 86400
```

The cache directory holds one file per query. Point it at a local disk, not a network mount. qcache assumes cheap reads, and it takes a lock on the whole directory, so two machines pointed at one shared path will spend their time contending for that lock instead of reading.

Maximum size is a ceiling on the directory total, not on any single entry. qcache checks the total after each write. When a write pushes it past the limit, eviction runs: least-recently-read entries go first, and enough of them go to bring the directory back under the ceiling.

The time-to-live clock starts at the write. Reads do not restart it, so a busy query and an idle one expire on the same schedule. The next lookup to touch an expired entry deletes it.
