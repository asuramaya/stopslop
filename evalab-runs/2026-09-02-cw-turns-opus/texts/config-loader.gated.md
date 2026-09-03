`load_json_config.py:99` — `load` takes `env_prefix="APP_"` and an optional `environ`, and the overlay runs on every return path (`_finish`, line 87), so an override wins over the file and also over a fallback to defaults.

Three judgment calls:

The value is read as the type the key already holds. `APP_PORT=5000` stays an int rather than becoming the string `"5000"`, and `APP_DEBUG` takes true/false/yes/no/on/off/1/0. A string that will not convert raises `ConfigError` naming the variable, so `APP_PORT=abc` says `APP_PORT: expected int` instead of failing later at the socket. This is the same coercion table `json_config.py` uses, so the two modules read the environment identically.

Any key is overridable, not just the three in `DEFAULTS` — you asked for "any key." A name with no existing value has no type to match, so it is read as JSON first and kept as a string when that fails: `APP_TAGS='["a","b"]'` arrives as a list, `APP_NAME=plain` as a string. The cost is that an unset key's type is decided by what the string looks like, so `APP_VERSION=1.0` arrives as a float. Baking every key into `DEFAULTS` removes that guesswork.

Port validation runs after the overlay, and the error names `APP_PORT` rather than the file when the environment is what set it. `APP_PORT=80` raises.

`env_prefix=None` skips the environment entirely; `env_prefix=""` raises `ValueError` rather than treating every variable in the process as config. `environ=` takes a dict for tests.

Unchanged: an unreadable file still raises, bad JSON still falls back at WARNING, and a `null` port still passes validation as "optional" — the environment cannot produce a null, so that gap is still only reachable from the file or from `defaults=`.
