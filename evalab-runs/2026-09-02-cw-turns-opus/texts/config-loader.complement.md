```python
"""Load a JSON config file, falling back to built-in defaults.

Precedence, lowest to highest: defaults, file contents, environment variables.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

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


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _coerce(raw: str, current: Any) -> Any:
    """Parse an env string to match the type of the value it replaces.

    Env vars are always strings, so `APP_PORT=9000` would otherwise shadow an
    int with "9000". Keys with no default, or a non-scalar default, stay strings.
    """
    if isinstance(current, bool):
        lowered = raw.strip().lower()
        if lowered in ("1", "true", "yes", "on"):
            return True
        if lowered in ("0", "false", "no", "off"):
            return False
        raise ConfigError(f"environment: cannot read {raw!r} as a boolean")
    if isinstance(current, int):
        try:
            return int(raw)
        except ValueError as exc:
            raise ConfigError(f"environment: cannot read {raw!r} as an integer") from exc
    if isinstance(current, float):
        try:
            return float(raw)
        except ValueError as exc:
            raise ConfigError(f"environment: cannot read {raw!r} as a number") from exc
    return raw


def _env_overrides(config: dict[str, Any], environ: dict[str, str]) -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    for key, value in config.items():
        raw = environ.get(ENV_PREFIX + key.upper())
        if raw is not None:
            overrides[key] = _coerce(raw, value)
    for name, raw in environ.items():
        if name.startswith(ENV_PREFIX):
            key = name[len(ENV_PREFIX):].lower()
            if key and key not in config:
                overrides[key] = raw
    return overrides


def _validate_port(config: dict[str, Any], source: str) -> None:
    if "port" not in config:
        return
    port = config["port"]
    # bool is a subclass of int, and True would otherwise pass as port 1.
    if isinstance(port, bool) or not isinstance(port, int):
        raise ConfigError(f"{source}: port must be an integer, got {type(port).__name__}")
    if not MIN_PORT <= port <= MAX_PORT:
        raise ConfigError(f"{source}: port {port} outside {MIN_PORT}-{MAX_PORT}")


def _finish(base: dict[str, Any], source: str, environ: dict[str, str]) -> dict[str, Any]:
    merged = _merge(base, _env_overrides(base, environ))
    _validate_port(merged, source)
    return merged


def load_config(
    path: str | Path,
    defaults: dict[str, Any] | None = None,
    environ: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return the config at `path` merged over `defaults`, then over the environment.

    A missing file, unparseable JSON, or a top-level value that is not an object
    all fall back to the defaults, logged at WARNING. An out-of-range port, or an
    env var that will not parse as the type it replaces, still raises ConfigError:
    the caller asked for something that cannot be served, and quietly substituting
    a different value would be worse than stopping.
    """
    base = DEFAULTS if defaults is None else defaults
    environ = dict(os.environ) if environ is None else environ
    path = Path(path)

    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.info("No config at %s; using defaults", path)
        return _finish(base, "defaults", environ)
    except OSError as exc:
        logger.warning("Cannot read %s (%s); using defaults", path, exc)
        return _finish(base, "defaults", environ)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("Invalid JSON in %s (%s); using defaults", path, exc)
        return _finish(base, "defaults", environ)

    if not isinstance(parsed, dict):
        logger.warning(
            "%s must contain a JSON object, got %s; using defaults", path, type(parsed).__name__
        )
        return _finish(base, "defaults", environ)

    return _finish(_merge(base, parsed), str(path), environ)
```
