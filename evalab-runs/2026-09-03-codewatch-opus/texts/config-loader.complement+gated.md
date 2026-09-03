```python
"""Load application config from a JSON file, falling back to built-in defaults."""

import json
import logging
import os
from copy import deepcopy

logger = logging.getLogger(__name__)

MIN_PORT = 1024
MAX_PORT = 65535
ENV_PREFIX = "APP_"

DEFAULT_CONFIG = {
    "host": "127.0.0.1",
    "port": 8080,
    "debug": False,
    "log_level": "INFO",
    "database": {
        "url": "sqlite:///app.db",
        "pool_size": 5,
    },
}


class ConfigError(Exception):
    """Raised when a config file exists but cannot be used."""


def _merge(base, override):
    """Recursively overlay override onto base, returning a new dict."""
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def _coerce(raw, current):
    """Parse an env string to match the type of the value it replaces."""
    if isinstance(current, bool):
        lowered = raw.strip().lower()
        if lowered in ("1", "true", "yes", "on"):
            return True
        if lowered in ("0", "false", "no", "off"):
            return False
        raise ConfigError(f"cannot read {raw!r} as a boolean")
    if isinstance(current, int):
        try:
            return int(raw)
        except ValueError as exc:
            raise ConfigError(f"cannot read {raw!r} as an integer") from exc
    if isinstance(current, float):
        try:
            return float(raw)
        except ValueError as exc:
            raise ConfigError(f"cannot read {raw!r} as a number") from exc
    if isinstance(current, (dict, list)):
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ConfigError(f"cannot read {raw!r} as JSON") from exc
    return raw


def _env_overrides(config, environ, prefix=ENV_PREFIX, _path=()):
    """Overlay APP_-prefixed env vars onto config, nesting with double underscores.

    APP_PORT sets "port"; APP_DATABASE__POOL_SIZE sets database.pool_size. Only
    keys already present are overridable, so a typo'd variable is reported
    rather than silently inventing a setting nothing reads.
    """
    result = deepcopy(config)
    for key, value in config.items():
        name = prefix + "__".join(_path + (key.upper(),))
        if isinstance(value, dict):
            result[key] = _env_overrides(value, environ, prefix, _path + (key.upper(),))
        elif name in environ:
            try:
                result[key] = _coerce(environ[name], value)
            except ConfigError as exc:
                raise ConfigError(f"{name}: {exc}") from exc
    return result


def _validate_port(config, source):
    if "port" not in config:
        return
    port = config["port"]
    # bool is a subclass of int, so True would otherwise pass as port 1
    if isinstance(port, bool) or not isinstance(port, int):
        raise ConfigError(f"{source}: port must be an integer, got {type(port).__name__}")
    if not MIN_PORT <= port <= MAX_PORT:
        raise ConfigError(f"{source}: port {port} outside {MIN_PORT}-{MAX_PORT}")


def load_config(path=None, defaults=None, environ=None):
    """Return the config at `path` merged over `defaults`, then env overrides.

    A missing, unreadable, malformed, or non-object config file is logged
    at WARNING and the defaults are returned instead of raising. A config
    whose merged values are invalid still raises ConfigError, since the
    caller asked for a setting the process cannot honour.
    """
    if defaults is None:
        defaults = DEFAULT_CONFIG
    if environ is None:
        environ = os.environ
    if path is None:
        path = environ.get("APP_CONFIG", "config.json")

    def _finish(config, source):
        config = _env_overrides(config, environ)
        _validate_port(config, source)
        return config

    try:
        with open(path, encoding="utf-8") as fh:
            loaded = json.load(fh)
    except FileNotFoundError:
        logger.info("No config at %s; using defaults", path)
        return _finish(deepcopy(defaults), "defaults")
    except OSError as exc:
        logger.warning("Cannot read config %s (%s); using defaults", path, exc)
        return _finish(deepcopy(defaults), "defaults")
    except json.JSONDecodeError as exc:
        logger.warning("Invalid JSON in %s (%s); using defaults", path, exc)
        return _finish(deepcopy(defaults), "defaults")

    if not isinstance(loaded, dict):
        logger.warning(
            "%s must contain a JSON object, got %s; using defaults",
            path,
            type(loaded).__name__,
        )
        return _finish(deepcopy(defaults), "defaults")

    return _finish(_merge(defaults, loaded), path)
```
