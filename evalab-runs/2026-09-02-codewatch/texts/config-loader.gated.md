`config_loader.py` already existed in the working tree (untracked, 60 lines) and already did what you described, so I verified it rather than rewriting it from scratch.

What it does — `load_config(path, defaults=None)` merges the file over `DEFAULTS` (`host`/`port`/`debug`), returns the defaults untouched on `FileNotFoundError`, and raises `ConfigError` (a `ValueError` subclass) for malformed JSON, a non-object top level, or a bad port. `validate_port` rejects non-ints, and rejects `bool` explicitly so `{"port": true}` doesn't sneak through as `1`.

Smoke test results, all passing:

- missing file → defaults
- `{"port": 9000, "host": "0.0.0.0"}` → merged
- `80` → outside 1024-65535
- `"9000"` → not an integer
- `true` → not an integer (bool guard works)
- `{ not json` → JSON decode error
- `[1,2]` → not an object

One gap I did fix: if you passed a custom `defaults` dict with no `port` and the file also omitted one, `config["port"]` raised a bare `KeyError` instead of `ConfigError`. Now it raises `ConfigError("... has no port and no default supplies one")` (config_loader.py:59).

Still unhandled, by design rather than oversight: `PermissionError` and `IsADirectoryError` propagate as-is instead of being wrapped. Say the word if you'd rather those become `ConfigError` too.
