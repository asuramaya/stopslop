```python
"""Load a JSON config file, falling back to built-in defaults."""

from __future__ import annotations

import copy
import json
import logging
import os
from pathlib import Path
from typing import Any, Mapping

log = logging.getLogger(__name__)

MIN_PORT = 1024
MAX_PORT = 65535
ENV_PREFIX = "APP_"

DEFAULTS: dict[str, Any] = {
    "host": "127.0.0.1",
    "port": 8080,
    "debug": False,
    "log_level": "INFO",
    "timeout_seconds": 30,
}


class ConfigError(Exception):
    """Raised when a config file exists but cannot be used."""


def _merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively overlay `override` onto `base`, returning a new dict."""
    merged = dict(base)
    for key, value in override.items():
        existing = merged.get(key)
        if isinstance(existing, Mapping) and isinstance(value, Mapping):
            merged[key] = _merge(existing, value)
        else:
            merged[key] = value
    return merged


def _coerce(raw: str, template: Any) -> Any:
    """Parse an env string into the type of the value it replaces.

    Env vars are always strings, so `APP_PORT=9000` has to become an int or
    validation will reject it. JSON is used for non-string targets, which also
    gives nested keys (`APP_LIMITS='{"rps": 5}'`) for free.
    """
    if isinstance(template, str) or template is None:
        return raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _apply_env(config: Mapping[str, Any], environ: Mapping[str, str], prefix: str) -> dict[str, Any]:
    """Overlay `PREFIX_KEY` env vars onto `config`, one level deep."""
    result = dict(config)
    for key in config:
        var = f"{prefix}{key.upper()}"
        if var in environ:
            result[key] = _coerce(environ[var], config[key])
            log.debug("Config key %r overridden by %s", key, var)
    return result


def _validate_port(config: Mapping[str, Any], source: str) -> None:
    """Check that `port`, if present, is an int in the unprivileged range."""
    if "port" not in config:
        return
    port = config["port"]
    # bool is an int subclass; True would otherwise slip through as port 1.
    if isinstance(port, bool) or not isinstance(port, int):
        raise ConfigError(f"{source}: port must be an integer, got {type(port).__name__}")
    if not MIN_PORT <= port <= MAX_PORT:
        raise ConfigError(f"{source}: port {port} outside {MIN_PORT}-{MAX_PORT}")


def load_config(
    path: str | Path,
    defaults: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
    env_prefix: str = ENV_PREFIX,
) -> dict[str, Any]:
    """Return config from env over `path` over `defaults`.

    A missing file is not an error, and neither is a corrupt one: both fall
    back to the defaults, with a warning logged for the corrupt case so the
    operator can see that their file was ignored. Unreadable files and
    semantically invalid values still raise ConfigError.

    Environment variables named `<env_prefix><KEY>` override any key that
    exists in the merged config; unknown vars are ignored so that a typo'd
    name fails loudly at the point of use rather than adding a dead key.
    Pass `env_prefix=""` to disable prefixing, or `environ={}` to skip the
    env layer entirely (useful in tests).
    """
    base = copy.deepcopy(dict(DEFAULTS if defaults is None else defaults))
    environ = os.environ if environ is None else environ
    path = Path(path)
    _validate_port(base, "defaults")

    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        log.info("No config at %s; using defaults", path)
        merged = base
    except OSError as exc:
        raise ConfigError(f"Cannot read config {path}: {exc}") from exc
    else:
        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError as exc:
            log.warning("Malformed JSON in %s (%s); falling back to defaults", path, exc)
            loaded = None

        if loaded is None:
            merged = base
        elif not isinstance(loaded, dict):
            log.warning(
                "Config %s is a JSON %s, not an object; falling back to defaults",
                path,
                type(loaded).__name__,
            )
            merged = base
        else:
            merged = _merge(base, loaded)

    merged = _apply_env(merged, environ, env_prefix)
    _validate_port(merged, "environment/" + str(path))
    return merged
```

Two notes on the env layer as written: it only overrides keys already present in the merged config, so `APP_NEW_THING` is silently dropped rather than inventing a key nothing reads; and a JSON file containing literal `null` is now treated the same as a corrupt file (defaults + warning), which is a behavior change from the previous version if you were using `null` as a whole-config value.
