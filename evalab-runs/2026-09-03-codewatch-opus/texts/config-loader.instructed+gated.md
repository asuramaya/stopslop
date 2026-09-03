```python
"""Load application config from a JSON file, with environment overrides and built-in defaults."""

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

DEFAULT_CONFIG: dict[str, Any] = {
    "host": "127.0.0.1",
    "port": 8080,
    "log_level": "INFO",
    "request_timeout_seconds": 30,
    "retries": 3,
}


class ConfigError(Exception):
    """Raised when a config file exists but cannot be used."""


def validate_port(port: Any) -> int:
    """Return `port` as an int, rejecting non-integers and reserved/out-of-range values."""
    if isinstance(port, bool) or not isinstance(port, int):
        raise ConfigError(f"port must be an integer, got {type(port).__name__}")
    if not MIN_PORT <= port <= MAX_PORT:
        raise ConfigError(f"port must be between {MIN_PORT} and {MAX_PORT}, got {port}")
    return port


def _coerce_to_default_type(key: str, text: str) -> Any:
    """Parse an environment string into the type the default for `key` uses."""
    default = DEFAULT_CONFIG[key]
    if isinstance(default, bool):
        lowered = text.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
        raise ConfigError(f"{ENV_PREFIX}{key.upper()} must be a boolean, got {text!r}")
    if isinstance(default, int):
        try:
            return int(text)
        except ValueError:
            raise ConfigError(f"{ENV_PREFIX}{key.upper()} must be an integer, got {text!r}") from None
    if isinstance(default, float):
        try:
            return float(text)
        except ValueError:
            raise ConfigError(f"{ENV_PREFIX}{key.upper()} must be a number, got {text!r}") from None
    return text


def env_overrides(environ: dict[str, str] | None = None) -> dict[str, Any]:
    """Read `APP_<KEY>` variables for known config keys, typed to match the defaults."""
    environ = os.environ if environ is None else environ
    overrides: dict[str, Any] = {}
    for key in DEFAULT_CONFIG:
        raw = environ.get(f"{ENV_PREFIX}{key.upper()}")
        if raw is not None:
            overrides[key] = _coerce_to_default_type(key, raw)
    return overrides


def merge_with_defaults(overrides: dict[str, Any]) -> dict[str, Any]:
    unknown = set(overrides) - set(DEFAULT_CONFIG)
    if unknown:
        logger.warning("ignoring unknown config keys: %s", ", ".join(sorted(unknown)))
    merged = dict(DEFAULT_CONFIG)
    merged.update({key: value for key, value in overrides.items() if key in DEFAULT_CONFIG})
    merged["port"] = validate_port(merged["port"])
    return merged


def load_config(path: str | Path, environ: dict[str, str] | None = None) -> dict[str, Any]:
    """Return the config at `path` merged over the defaults, with environment last.

    A missing or unparseable file yields the defaults; a parseable file whose
    contents are wrong is still an error, since that is a mistake worth fixing.
    """
    path = Path(path)
    from_file: dict[str, Any] = {}
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.info("no config at %s, using defaults", path)
        raw = None
    except OSError as exc:
        raise ConfigError(f"could not read config at {path}: {exc}") from exc

    if raw is not None:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning("invalid JSON in %s (%s), using defaults", path, exc)
            parsed = {}
        if not isinstance(parsed, dict):
            raise ConfigError(f"expected a JSON object in {path}, got {type(parsed).__name__}")
        from_file = parsed

    return merge_with_defaults({**from_file, **env_overrides(environ)})
```
