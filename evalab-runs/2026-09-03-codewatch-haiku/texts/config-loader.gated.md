```python
import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "debug": False,
    "timeout": 30,
    "max_retries": 3,
    "log_level": "INFO",
    "port": 8080,
}

ENV_PREFIX = "APP_CONFIG_"


class ConfigLoader:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load config from file, apply env overrides, or return defaults if file is missing or malformed."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    file_config = json.load(f)
                    config = {**DEFAULT_CONFIG, **file_config}
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(
                    f"Failed to load config from {self.config_path}: {e}. "
                    "Using defaults."
                )
                config = DEFAULT_CONFIG.copy()
        else:
            config = DEFAULT_CONFIG.copy()
        
        # Apply environment variable overrides
        config = self._apply_env_overrides(config)
        
        self._validate_config(config)
        return config

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to config."""
        for key in config:
            env_key = f"{ENV_PREFIX}{key.upper()}"
            if env_key in os.environ:
                value = os.environ[env_key]
                # Try to convert to appropriate type
                if isinstance(config[key], bool):
                    config[key] = value.lower() in ("true", "1", "yes")
                elif isinstance(config[key], int):
                    try:
                        config[key] = int(value)
                    except ValueError:
                        logger.warning(f"Could not convert {env_key}={value} to int")
                else:
                    config[key] = value
        return config

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate config values."""
        if "port" in config:
            port = config["port"]
            if not isinstance(port, int) or port < 1024 or port > 65535:
                raise ValueError(
                    f"port must be an integer between 1024 and 65535, got {port}"
                )

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value by key."""
        return self.config.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        """Get the entire config dictionary."""
        return self.config.copy()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    loader = ConfigLoader()
    print(loader.get_all())
```
