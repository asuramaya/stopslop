```python
"""Load a JSON config file with env-var overrides, falling back to built-in defaults."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Mapping

logger = logging.getLogger(__name__)

MIN_PORT = 1024
MAX_PORT = 65535
ENV_PREFIX = "APP_"
NESTED_SEP = "__"

DEFAULTS: dict[str, Any] = {
    "host": "127.0.0.1",
    "port": 8080,
    "debug": False,
    "log_level": "INFO",
    "timeout_seconds": 30,
}

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}


class ConfigError(Exception):
    """Raised when even the defaults fail validation."""


def _merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively merge override into base, returning a new dict."""
    merged = dict(base)
    for key, value in override.items():
        current = merged.get(key)
        if isinstance(current, Mapping) and isinstance(value, Mapping):
            merged[key] = _merge(current, value)
        else:
            merged[key] = value
    return merged


def _coerce(raw: str, current: Any) -> Any:
    """Interpret an env string in the shape of the value it is replacing.

    Known keys are coerced to the existing value's type so `APP_PORT=9000` stays
    an int. Unknown keys are parsed as JSON when possible, else left as a string.
    """
    if isinstance(current, bool):
        lowered = raw.strip().lower()
        if lowered in _TRUE:
            return True
        if lowered in _FALSE:
            return False
        raise ValueError(f"expected a boolean, got {raw!r}")
    if isinstance(current, int):
        return int(raw.strip())
    if isinstance(current, float):
        return float(raw.strip())
    if isinstance(current, str):
        return raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _env_overrides(
    config: Mapping[str, Any],
    environ: Mapping[str, str],
    prefix: str,
) -> dict[str, Any]:
    """Build a nested override dict from `prefix`-scoped environment variables.

    `APP_PORT` overrides "port"; `APP_DB__HOST` overrides ("db", "host"). A value
    that cannot be coerced is logged and skipped rather than sinking the load.
    """
    overrides: dict[str, Any] = {}
    for name, raw in environ.items():
        if not name.startswith(prefix) or name == prefix:
            continue
        path = [part.lower() for part in name[len(prefix):].split(NESTED_SEP)]
        if not all(path):
            logger.warning("Ignoring malformed env override %s", name)
            continue

        current: Any = config
        for part in path:
            current = current.get(part) if isinstance(current, Mapping) else None
        try:
            value = _coerce(raw, current)
        except ValueError as exc:
            logger.warning("Ignoring env override %s (%s)", name, exc)
            continue

        cursor = overrides
        for part in path[:-1]:
            slot = cursor.get(part)
            if not isinstance(slot, dict):
                slot = {}
                cursor[part] = slot
            cursor = slot
        cursor[path[-1]] = value
    return overrides


def _validate(config: Mapping[str, Any], source: str) -> None:
    """Check invariants that a merged config must satisfy."""
    if "port" not in config:
        raise ConfigError(f"{source}: missing required key 'port'")

    port = config["port"]
    # bool is a subclass of int, so True would otherwise sneak through as 1.
    if isinstance(port, bool) or not isinstance(port, int):
        raise ConfigError(f"{source}: 'port' must be an integer, got {type(port).__name__}")
    if not MIN_PORT <= port <= MAX_PORT:
        raise ConfigError(f"{source}: 'port' must be between {MIN_PORT} and {MAX_PORT}, got {port}")


def load_config(
    path: str | Path,
    defaults: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
    env_prefix: str = ENV_PREFIX,
) -> dict[str, Any]:
    """Return the config for `path`: defaults < file < environment, validated.

    This function does not raise for bad external input. A file that is missing,
    unreadable, malformed, not a JSON object, or that fails validation is logged
    and skipped; so is any env override that fails validation. The only
    ConfigError that escapes is a failure in the defaults themselves, which is a
    programming error. Pass `environ={}` to disable env overrides entirely.
    """
    base = DEFAULTS if defaults is None else defaults
    _validate(base, "defaults")  # a broken fallback is worse than a broken file
    environ = os.environ if environ is None else environ
    path = Path(path)

    from_file: Mapping[str, Any] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.info("No config at %s; using defaults", path)
    except OSError as exc:
        logger.warning("Could not read %s (%s); using defaults", path, exc)
    else:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning("Invalid JSON in %s (%s); using defaults", path, exc)
        else:
            if isinstance(data, dict):
                from_file = data
            else:
                logger.warning(
                    "Expected a JSON object in %s, got %s; using defaults",
                    path,
                    type(data).__name__,
                )

    config = _merge(base, from_file)
    try:
        _validate(config, str(path))
    except ConfigError as exc:
        logger.warning("%s; using defaults", exc)
        config = dict(base)

    overrides = _env_overrides(config, environ, env_prefix)
    if not overrides:
        return config

    with_env = _merge(config, overrides)
    try:
        _validate(with_env, f"environment ({env_prefix}*)")
    except ConfigError as exc:
        logger.warning("%s; ignoring env overrides", exc)
        return config
    return with_env
```

Two things about the env layer worth knowing before it ships:

- Coercion keys off the *current* value's type, so an override for a key absent from both the defaults and the file gets JSON-parsed (`APP_RETRIES=3` → int `3`, `APP_NAME=bob` → str). That's a guess; if you want unknown keys rejected instead, make `_coerce` raise when `current is None`.
- A bad env override is dropped whole-cloth: if `APP_PORT=80` fails the range check, *all* overrides in that batch are discarded, not just the offending one. Per-key rollback would be more surgical but harder to reason about — this way the returned config is always one of two known states.
