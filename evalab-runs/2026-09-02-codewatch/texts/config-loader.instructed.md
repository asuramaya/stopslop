```python
"""Load and validate application configuration from a JSON file."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MIN_PORT = 1024
MAX_PORT = 65535

DEFAULTS = {
    "host": "127.0.0.1",
    "port": 8080,
    "debug": False,
}


class ConfigError(ValueError):
    """Raised when a config file exists but cannot be used."""


def load_config(path):
    """Return config from `path`, merged over the defaults.

    A missing file is not an error: the defaults are returned as-is. A file
    that exists but is unreadable, malformed, or invalid raises ConfigError.
    """
    path = Path(path)
    config = dict(DEFAULTS)

    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.info("No config at %s; using defaults", path)
        return config
    except OSError as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{path} is not valid JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ConfigError(f"{path} must contain a JSON object")

    config.update(parsed)
    config["port"] = validate_port(config["port"])
    return config


def validate_port(port):
    """Return `port` as an int, or raise ConfigError if it is out of range."""
    # bool is an int subclass, and True would otherwise pass as port 1.
    if isinstance(port, bool) or not isinstance(port, int):
        raise ConfigError(f"port must be an integer, got {type(port).__name__}")
    if not MIN_PORT <= port <= MAX_PORT:
        raise ConfigError(f"port must be between {MIN_PORT} and {MAX_PORT}, got {port}")
    return port
```
