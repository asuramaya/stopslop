```python
import copy
import json
import os
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    "debug": False,
    "host": "localhost",
    "port": 8000,
    "log_level": "INFO",
    "timeout": 30,
    "database": {
        "engine": "sqlite",
        "path": ":memory:",
    },
}

ENV_PREFIX = "APP_"


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration values."""
    if "port" in config:
        port = config["port"]
        if not isinstance(port, int):
            raise ValueError(f"port must be an integer, got {type(port).__name__}")
        if not (1024 <= port <= 65535):
            raise ValueError(f"port must be between 1024 and 65535, got {port}")
    return config


def parse_env_value(value: str) -> Any:
    """Parse environment variable value to appropriate type."""
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """Override config values with environment variables prefixed with APP_."""
    for key, value in config.items():
        if isinstance(value, dict):
            continue
        env_key = ENV_PREFIX + key.upper()
        if env_key in os.environ:
            config[key] = parse_env_value(os.environ[env_key])
    return config


def load_config(config_path: str | Path = "config.json") -> Dict[str, Any]:
    """Load JSON config file with fallback to defaults when missing or invalid."""
    config_path = Path(config_path)
    
    if not config_path.exists():
        config = copy.deepcopy(DEFAULT_CONFIG)
    else:
        try:
            with open(config_path) as f:
                user_config = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Failed to parse config at {config_path}: {e}, using defaults")
            return copy.deepcopy(DEFAULT_CONFIG)
        
        config = copy.deepcopy(DEFAULT_CONFIG)
        config.update(user_config)
    
    try:
        validate_config(config)
    except ValueError as e:
        print(f"Invalid config at {config_path}: {e}, using defaults")
        return copy.deepcopy(DEFAULT_CONFIG)
    
    apply_env_overrides(config)
    return config


def get_config(config_path: str | Path | None = None) -> Dict[str, Any]:
    """Load config from path, environment variable, or default location."""
    if config_path is None:
        config_path = os.getenv("CONFIG_PATH", "config.json")
    return load_config(config_path)


if __name__ == "__main__":
    config = get_config()
    print("Configuration loaded:")
    print(json.dumps(config, indent=2))
```
