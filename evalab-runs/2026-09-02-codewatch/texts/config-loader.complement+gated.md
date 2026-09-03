```python
"""Load a JSON config from disk, with defaults and port validation."""

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

MIN_PORT = 1024
MAX_PORT = 65535

DEFAULTS = {
    "host": "127.0.0.1",
    "port": 8080,
    "debug": False,
}


class ConfigError(ValueError):
    """The config file exists but its contents cannot be used."""


def _validate_port(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"port must be an integer, got {type(value).__name__}")
    if not MIN_PORT <= value <= MAX_PORT:
        raise ConfigError(f"port must be between {MIN_PORT} and {MAX_PORT}, got {value}")
    return value


def load_config(path=None, defaults=None):
    """Return the config at *path*, merged over *defaults*.

    A missing file is not an error; the defaults stand on their own. A file
    that exists but is unreadable or malformed is an error, since silently
    ignoring it would hide a typo in the operator's config.
    """
    path = Path(path) if path is not None else Path("config.json")
    config = dict(DEFAULTS if defaults is None else defaults)

    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        log.info("no config at %s, using defaults", path)
        return config

    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{path} is not valid JSON: {exc}") from exc

    if not isinstance(loaded, dict):
        raise ConfigError(f"{path} must contain a JSON object, got {type(loaded).__name__}")

    config.update(loaded)
    config["port"] = _validate_port(config["port"])
    return config
```
