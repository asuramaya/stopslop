```python
"""Load a JSON config from disk, falling back to built-in defaults."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MIN_PORT = 1024
MAX_PORT = 65535

DEFAULTS = {
    "host": "127.0.0.1",
    "port": 8080,
    "log_level": "INFO",
}


class ConfigError(ValueError):
    """Raised when a config file exists but is unusable."""


def load_config(path):
    """Return the config at `path`, merged over DEFAULTS.

    A missing file yields the defaults. Malformed JSON, a non-object
    top level, or an out-of-range port raises ConfigError.
    """
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.info("No config at %s; using defaults", path)
        return dict(DEFAULTS)

    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{path} is not valid JSON: {exc}") from exc

    if not isinstance(loaded, dict):
        raise ConfigError(f"{path} must contain a JSON object, got {type(loaded).__name__}")

    config = {**DEFAULTS, **loaded}
    config["port"] = validate_port(config["port"])
    return config


def validate_port(port):
    """Return `port` as an int, or raise ConfigError if it is not a usable port."""
    if isinstance(port, bool) or not isinstance(port, int):
        raise ConfigError(f"port must be an integer, got {port!r}")
    if not MIN_PORT <= port <= MAX_PORT:
        raise ConfigError(f"port must be between {MIN_PORT} and {MAX_PORT}, got {port}")
    return port
```
