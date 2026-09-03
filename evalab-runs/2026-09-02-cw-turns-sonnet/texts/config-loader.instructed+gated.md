```python
"""Load JSON config from disk, falling back to defaults if the file is absent or malformed.

Any key can be overridden by an environment variable named CONFIG_<KEY> (uppercased).
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_CONFIG: dict[str, Any] = {
    "host": "localhost",
    "port": 8080,
    "debug": False,
    "log_level": "INFO",
    "max_connections": 100,
}

MIN_PORT = 1024
MAX_PORT = 65535

ENV_PREFIX = "CONFIG_"


def _validate_port(port: Any) -> int:
    if not isinstance(port, int) or isinstance(port, bool):
        raise ValueError(f"'port' must be an integer, got {type(port).__name__}")
    if not MIN_PORT <= port <= MAX_PORT:
        raise ValueError(f"'port' must be between {MIN_PORT} and {MAX_PORT}, got {port}")
    return port


def _coerce(key: str, raw: str, default: Any) -> Any:
    if isinstance(default, bool):
        return raw.strip().lower() in ("1", "true", "yes", "on")
    if isinstance(default, int):
        try:
            return int(raw)
        except ValueError:
            raise ValueError(f"environment override for '{key}' must be an integer, got {raw!r}")
    return raw


def _apply_env_overrides(config: dict[str, Any]) -> dict[str, Any]:
    for key in config:
        env_name = ENV_PREFIX + key.upper()
        if env_name in os.environ:
            raw = os.environ[env_name]
            config[key] = _coerce(key, raw, config[key])
            logger.info("Config key '%s' overridden by environment variable %s", key, env_name)
    return config


def load_config(path: str | Path) -> dict[str, Any]:
    path = Path(path)

    if not path.exists():
        logger.warning("Config file %s not found, using defaults", path)
        config = dict(DEFAULT_CONFIG)
        config = _apply_env_overrides(config)
        config["port"] = _validate_port(config["port"])
        return config

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.error("Config file %s is not valid JSON (%s), using defaults", path, e)
        data = {}

    if not isinstance(data, dict):
        logger.error("Config file %s must contain a JSON object, got %s; using defaults", path, type(data).__name__)
        data = {}

    config = dict(DEFAULT_CONFIG)
    config.update(data)
    config = _apply_env_overrides(config)
    config["port"] = _validate_port(config["port"])

    return config


def save_config(path: str | Path, config: dict[str, Any]) -> None:
    path = Path(path)
    with path.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
```
