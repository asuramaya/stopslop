```python
"""Load application config from a JSON file, falling back to built-in defaults."""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "host": "127.0.0.1",
    "port": 8080,
    "log_level": "INFO",
    "max_connections": 100,
    "request_timeout_seconds": 30.0,
}

ENV_PREFIX = "APP_"
MIN_PORT = 1024
MAX_PORT = 65535


class ConfigError(Exception):
    """Raised when a config file exists but cannot be read or validated."""


def _validate_port(port, source):
    if isinstance(port, bool) or not isinstance(port, int):
        raise ConfigError(f"{source}: port must be an integer, got {type(port).__name__}")
    if not MIN_PORT <= port <= MAX_PORT:
        raise ConfigError(f"{source}: port {port} is outside {MIN_PORT}-{MAX_PORT}")


def _coerce(raw, current, name):
    """Parse an env var string into the type of the value it overrides."""
    if isinstance(current, bool):
        lowered = raw.strip().lower()
        if lowered in ("1", "true", "yes", "on"):
            return True
        if lowered in ("0", "false", "no", "off"):
            return False
        raise ConfigError(f"{name}: expected a boolean, got {raw!r}")
    for kind in (int, float):
        if isinstance(current, kind) and not isinstance(current, bool):
            try:
                return kind(raw)
            except ValueError as exc:
                raise ConfigError(f"{name}: expected {kind.__name__}, got {raw!r}") from exc
    return raw


def _apply_env_overrides(config, environ):
    """Override any key with APP_<KEY>, e.g. APP_PORT=9000 sets `port`."""
    for key in config:
        name = ENV_PREFIX + key.upper()
        if name in environ:
            config[key] = _coerce(environ[name], config[key], name)
            logger.info("Config key %s overridden by %s", key, name)
    return config


def load_config(path, defaults=None, environ=None):
    """Return defaults merged with the JSON object at `path`, then with the env.

    A missing file, malformed JSON, or a top-level value that is not an object
    all yield the defaults unchanged, with a warning logged. An unreadable file
    (permissions, I/O) raises, since that is a broken deployment rather than an
    absent one.

    Environment variables win over the file: APP_PORT=9000 sets `port` to 9000.
    Each override is parsed into the type of the value it replaces, so a
    non-numeric APP_PORT raises ConfigError rather than smuggling a string in.
    A port outside 1024-65535 also raises, from whichever source supplied it: a
    caller that asked for a specific port and got a bad one should hear about it
    rather than quietly serve on 8080.
    """
    base = dict(DEFAULT_CONFIG if defaults is None else defaults)
    path = Path(path)

    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.info("No config at %s; using defaults", path)
        text = None
    except OSError as exc:
        raise ConfigError(f"cannot read config at {path}: {exc}") from exc

    if text is not None:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning("Invalid JSON in %s (%s); using defaults", path, exc)
            parsed = {}

        if not isinstance(parsed, dict):
            logger.warning(
                "%s must hold a JSON object, got %s; using defaults", path, type(parsed).__name__
            )
            parsed = {}

        unknown = set(parsed) - set(base)
        if unknown:
            logger.warning(
                "Ignoring unknown config keys in %s: %s", path, ", ".join(sorted(unknown))
            )

        base.update({key: value for key, value in parsed.items() if key in base})

    _apply_env_overrides(base, os.environ if environ is None else environ)

    if "port" in base:
        _validate_port(base["port"], path)
    return base
```
