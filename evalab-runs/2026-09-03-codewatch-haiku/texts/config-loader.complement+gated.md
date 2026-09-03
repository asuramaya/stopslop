```python
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "host": "localhost",
    "port": 8080,
    "debug": False,
    "timeout": 30,
    "max_retries": 3,
}

ENV_PREFIX = "CONFIG_"


class ConfigLoader:
    def __init__(self, config_path: str | None = None):
        self.config_path = Path(config_path) if config_path else Path("config.json")
        self._config: dict[str, Any] | None = None

    @property
    def config(self) -> dict[str, Any]:
        if self._config is None:
            self._config = self.load()
        return self._config

    def load(self) -> dict[str, Any]:
        if not self.config_path.exists():
            logger.warning(f"Config file not found at {self.config_path}, using defaults")
            config = DEFAULT_CONFIG.copy()
        else:
            try:
                with open(self.config_path) as f:
                    loaded = json.load(f)
                config = {**DEFAULT_CONFIG, **loaded}
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load config from {self.config_path}: {e}, using defaults")
                config = DEFAULT_CONFIG.copy()
        
        self._apply_env_overrides(config)
        self._validate(config)
        return config

    def _apply_env_overrides(self, config: dict[str, Any]) -> None:
        for key in config:
            env_key = f"{ENV_PREFIX}{key.upper()}"
            if env_key in os.environ:
                env_value = os.environ[env_key]
                if isinstance(config[key], bool):
                    config[key] = env_value.lower() in ("true", "1", "yes")
                elif isinstance(config[key], int):
                    config[key] = int(env_value)
                else:
                    config[key] = env_value

    def _validate(self, config: dict[str, Any]) -> None:
        port = config.get("port")
        if not isinstance(port, int):
            raise ValueError(f"port must be an integer, got {type(port).__name__}")
        if not (1024 <= port <= 65535):
            raise ValueError(f"port must be between 1024 and 65535, got {port}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def reload(self) -> None:
        self._config = None


if __name__ == "__main__":
    loader = ConfigLoader()
    print(loader.config)
```
