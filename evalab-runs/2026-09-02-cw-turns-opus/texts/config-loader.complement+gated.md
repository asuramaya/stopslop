```python
"""Load a JSON config file, falling back to built-in defaults."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PORT_MIN = 1024
PORT_MAX = 65535
ENV_PREFIX = "APP_"

DEFAULTS: dict[str, Any] = {
    "host": "127.0.0.1",
    "port": 8080,
    "workers": 4,
    "log_level": "INFO",
    "features": [],
}


class ConfigError(ValueError):
    """Raised when a config value cannot be used."""


def _defaults() -> dict[str, Any]:
    return json.loads(json.dumps(DEFAULTS))


def _check_port(value: Any, source: str) -> None:
    # bool is an int subclass, so True would otherwise pass as a port number.
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"port in {source} must be an integer, got {type(value).__name__}")
    if not PORT_MIN <= value <= PORT_MAX:
        raise ConfigError(f"port in {source} must be {PORT_MIN}-{PORT_MAX}, got {value}")


def _coerce(raw: str, template: Any, name: str) -> Any:
    """Parse an env string into the type its default demonstrates.

    Environment values arrive as text, so a list or number default means the
    override has to be JSON; a string default is taken verbatim, which keeps
    APP_HOST=localhost working without quoting.
    """
    if isinstance(template, str):
        return raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{ENV_PREFIX}{name.upper()} must be JSON: {exc}") from exc


def _env_overrides(
    keys: dict[str, Any], environ: dict[str, str] | None = None
) -> dict[str, Any]:
    env = os.environ if environ is None else environ
    found = {}
    for name, template in keys.items():
        raw = env.get(f"{ENV_PREFIX}{name.upper()}")
        if raw is not None:
            found[name] = _coerce(raw, template, name)
    return found


def load_config(
    path: str | Path,
    defaults: dict[str, Any] | None = None,
    environ: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return defaults merged with the JSON object at *path*, then with the env.

    A missing, unreadable, malformed, or non-object file yields the defaults
    unchanged, logged at WARNING. Values that survive to the end are still held
    to the checks below, so a bad port raises rather than being silently
    swapped for 8080. Environment variables are named APP_<KEY> and win over
    both the file and the defaults.
    """
    merged = _defaults() if defaults is None else dict(defaults)
    path = Path(path)
    port_source = "defaults"

    def finish() -> dict[str, Any]:
        overrides = _env_overrides(merged, environ)
        if overrides:
            logger.info("Environment overrides: %s", ", ".join(sorted(overrides)))
        merged.update(overrides)
        _check_port(merged["port"], f"{ENV_PREFIX}PORT" if "port" in overrides else port_source)
        return merged

    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.info("No config at %s; using defaults", path)
        return finish()
    except OSError as exc:
        logger.warning("Cannot read config %s (%s); using defaults", path, exc)
        return finish()

    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("Invalid JSON in %s (%s); using defaults", path, exc)
        return finish()

    if not isinstance(loaded, dict):
        logger.warning(
            "Config %s must hold an object, got %s; using defaults", path, type(loaded).__name__
        )
        return finish()

    unknown = set(loaded) - set(merged)
    if unknown:
        logger.warning("Ignoring unknown keys in %s: %s", path, ", ".join(sorted(unknown)))

    merged.update({k: v for k, v in loaded.items() if k in merged})
    if "port" in loaded:
        port_source = str(path)
    return finish()
```
