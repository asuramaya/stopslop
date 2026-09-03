```python
"""Load a JSON config file from disk, falling back to defaults if missing."""
import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_CONFIG: dict[str, Any] = {
    "host": "localhost",
    "port": 8080,
    "debug": False,
    "log_level": "info",
    "max_connections": 100,
}

ENV_PREFIX = "APP_CONFIG_"

MIN_PORT = 1024
MAX_PORT = 65535


def _validate_port(port: Any) -> None:
    if not isinstance(port, int) or isinstance(port, bool):
        raise ValueError(f"port must be an integer, got {port!r}")
    if not (MIN_PORT <= port <= MAX_PORT):
        raise ValueError(f"port must be between {MIN_PORT} and {MAX_PORT}, got {port}")


def _coerce_env_value(key: str, raw: str, current: Any) -> Any:
    if isinstance(current, bool):
        return raw.strip().lower() in ("1", "true", "yes", "on")
    if isinstance(current, int):
        try:
            return int(raw)
        except ValueError as exc:
            raise ValueError(f"environment override for {key!r} must be an integer, got {raw!r}") from exc
    return raw


def _apply_env_overrides(config: dict[str, Any]) -> dict[str, Any]:
    for key, value in config.items():
        env_name = ENV_PREFIX + key.upper()
        if env_name in os.environ:
            config[key] = _coerce_env_value(key, os.environ[env_name], value)
    return config


def load_config(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        return _apply_env_overrides(dict(DEFAULT_CONFIG))

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            logger.warning("config file %s has invalid JSON (%s), using defaults", path, exc)
            return _apply_env_overrides(dict(DEFAULT_CONFIG))

    if not isinstance(data, dict):
        logger.warning("config file %s does not contain a JSON object, using defaults", path)
        return _apply_env_overrides(dict(DEFAULT_CONFIG))

    config = dict(DEFAULT_CONFIG)
    config.update(data)
    config = _apply_env_overrides(config)
    _validate_port(config["port"])
    return config


def get_config_value(config: dict[str, Any], key: str) -> Any:
    if key not in config:
        raise KeyError(f"unknown config key: {key}")
    return config[key]


def save_config(config: dict[str, Any], path: str) -> None:
    _validate_port(config["port"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, sort_keys=True)
```
