Added. `APP_<KEY>` env vars now overlay the config, and they win over both the file and the defaults.

`apply_env` at `config_loader.py:67` runs on all three exit paths, so an override applies whether the file loaded, was missing, or was malformed. It's a separate function taking an `environ` argument (defaulting to `os.environ`), so tests can pass a dict instead of mutating the process. `load_config` gained the same optional argument.

Values coerce to the type the key already holds: `APP_PORT=7000` becomes an int, `APP_DEBUG` accepts `1/true/yes/on` and `0/false/no/off`, a dict or list default parses as JSON, everything else stays a string. A key nothing has ever defined (`APP_REGION`) is accepted as a plain string, since there's no template to coerce against — that's the "any key" part of your ask.

Verified:

- `APP_PORT=7000` over a file saying 9000 → 7000; over defaults with no file → 7000
- `APP_HOST` with no file → overrides the default host
- `APP_DEBUG=yes` → `True`, `APP_DEBUG=OFF` → `False`
- `APP_REGION=eu-west-1` → new key, string
- unprefixed `PORT=1` ignored; bare `APP_=x` ignored
- `APP_PORT=80` → outside the range; `APP_PORT=abc` and `APP_DEBUG=maybe` → parse errors

One inconsistency you should decide on: a bad env var **raises**, while a bad file falls back. I chose that deliberately — someone who exports `APP_PORT=abc` is actively trying to change the port, and silently booting on 8080 hides their typo, where a malformed file is often stale junk on disk. But it does mean the module now has two different answers to "input is garbage," and if the fallback behaviour you asked for last turn was about not crashing at startup generally, this reintroduces the crash through a different door. Tell me and I'll make bad env vars warn and fall through as well.

Also worth knowing: the env is read on each `load_config` call, not cached at import, so a process that reloads config picks up changes. And `MIN_PORT = 1024` still applies to env overrides, so `APP_PORT=443` is refused the same as a file saying 443.
