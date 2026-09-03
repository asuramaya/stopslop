```python
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "debug": False,
    "timeout": 30,
    "max_retries": 3,
    "log_level": "INFO",
    "host": "localhost",
    "port": 8000,
}


class ConfigValidationError(ValueError):
    pass


class ConfigLoader:
    def __init__(self, config_path: str | Path = "config.json", env_prefix: str = "APP_"):
        self.config_path = Path(config_path)
        self.env_prefix = env_prefix
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    file_config = json.load(f)
                merged = {**DEFAULT_CONFIG, **file_config}
            except json.JSONDecodeError as e:
                logger.warning(f"Malformed JSON in {self.config_path}: {e}. Using defaults.")
                merged = DEFAULT_CONFIG.copy()
            except IOError as e:
                logger.warning(f"Failed to read {self.config_path}: {e}. Using defaults.")
                merged = DEFAULT_CONFIG.copy()
        else:
            merged = DEFAULT_CONFIG.copy()

        merged = self._apply_env_overrides(merged)
        self._validate_config(merged)
        return merged

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        for key in config:
            env_key = f"{self.env_prefix}{key.upper()}"
            if env_key in os.environ:
                env_value = os.environ[env_key]
                config[key] = self._parse_env_value(env_value, config[key])
        return config

    def _parse_env_value(self, env_str: str, default_value: Any) -> Any:
        if isinstance(default_value, bool):
            return env_str.lower() in ("true", "1", "yes")
        elif isinstance(default_value, int):
            try:
                return int(env_str)
            except ValueError:
                logger.warning(f"Could not parse '{env_str}' as int, using default")
                return default_value
        elif isinstance(default_value, float):
            try:
                return float(env_str)
            except ValueError:
                logger.warning(f"Could not parse '{env_str}' as float, using default")
                return default_value
        return env_str

    def _validate_config(self, config: Dict[str, Any]) -> None:
        port = config.get("port")
        if not isinstance(port, int):
            raise ConfigValidationError(
                f"port must be an integer, got {type(port).__name__}"
            )
        if not (1024 <= port <= 65535):
            raise ConfigValidationError(f"port must be between 1024 and 65535, got {port}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.config[key]

    def __contains__(self, key: str) -> bool:
        return key in self.config
```
