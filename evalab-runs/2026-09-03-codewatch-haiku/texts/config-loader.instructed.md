```python
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_CONFIG: dict[str, Any] = {
    "debug": False,
    "timeout": 30,
    "max_retries": 3,
    "log_level": "INFO",
    "port": 8000,
}


class Config:
    ENV_PREFIX = "CONFIG_"

    def __init__(self, config_path: str | Path, defaults: dict[str, Any] | None = None):
        self.config_path = Path(config_path)
        self.defaults = defaults or DEFAULT_CONFIG
        self.data = self._load()
        self._apply_env_overrides()
        self._validate()

    def _load(self) -> dict[str, Any]:
        if not self.config_path.exists():
            logger.warning(f"Config file not found at {self.config_path}, using defaults")
            return self.defaults.copy()

        try:
            with open(self.config_path) as f:
                loaded = json.load(f)
                merged = self.defaults.copy()
                merged.update(loaded)
                logger.info(f"Config loaded from {self.config_path}")
                return merged
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load config: {e}, falling back to defaults")
            return self.defaults.copy()

    def _apply_env_overrides(self) -> None:
        for key in self.data:
            env_var = f"{self.ENV_PREFIX}{key.upper()}"
            if env_var in os.environ:
                value = os.environ[env_var]
                value = self._coerce_type(value, type(self.data[key]))
                self.data[key] = value
                logger.info(f"Config key '{key}' overridden by {env_var}")

    def _coerce_type(self, value: str, target_type: type) -> Any:
        if target_type is bool:
            return value.lower() in ("true", "1", "yes", "on")
        elif target_type is int:
            return int(value)
        elif target_type is float:
            return float(value)
        return value

    def _validate(self) -> None:
        try:
            if "port" in self.data:
                port = self.data["port"]
                if not isinstance(port, int):
                    raise ValueError(f"port must be an integer, got {type(port).__name__}")
                if not (1024 <= port <= 65535):
                    raise ValueError(f"port must be between 1024 and 65535, got {port}")
        except ValueError as e:
            logger.error(f"Validation failed: {e}, falling back to defaults")
            self.data = self.defaults.copy()

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __contains__(self, key: str) -> bool:
        return key in self.data

    def __repr__(self) -> str:
        return f"Config({self.data})"
```
