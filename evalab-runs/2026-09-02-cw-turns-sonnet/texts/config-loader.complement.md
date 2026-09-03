```python
import json
import os
from pathlib import Path

DEFAULT_CONFIG = {
    "host": "localhost",
    "port": 8080,
    "debug": False,
    "log_level": "info",
    "max_connections": 100,
}

ENV_PREFIX = "APP_CONFIG_"


def load_config(path):
    """Load a JSON config file, falling back to defaults when missing or malformed."""
    config_path = Path(path)

    if not config_path.exists():
        merged = dict(DEFAULT_CONFIG)
    else:
        with config_path.open("r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as exc:
                print(f"config at {path} is not valid JSON ({exc}); using defaults")
                data = {}

        if not isinstance(data, dict):
            raise ValueError(f"config at {path} must be a JSON object")

        merged = dict(DEFAULT_CONFIG)
        merged.update(data)

    _apply_env_overrides(merged)
    _validate_port(merged["port"])
    return merged


def _apply_env_overrides(config):
    for key in config:
        env_name = ENV_PREFIX + key.upper()
        if env_name not in os.environ:
            continue
        raw = os.environ[env_name]
        default = DEFAULT_CONFIG.get(key)
        if isinstance(default, bool):
            config[key] = raw.lower() in ("1", "true", "yes")
        elif isinstance(default, int):
            config[key] = int(raw)
        else:
            config[key] = raw


def _validate_port(port):
    if not isinstance(port, int) or isinstance(port, bool):
        raise ValueError(f"port must be an integer, got {port!r}")
    if not 1024 <= port <= 65535:
        raise ValueError(f"port must be between 1024 and 65535, got {port}")
```
