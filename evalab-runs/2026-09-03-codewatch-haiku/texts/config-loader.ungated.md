```python
import json
import os
from typing import Any, Dict, Optional

DEFAULT_CONFIG = {
    "debug": False,
    "host": "localhost",
    "port": 8000,
    "timeout": 30,
    "max_retries": 3,
    "log_level": "INFO",
}

ENV_PREFIX = "APP_"


class Config:
    """Load and manage application configuration from JSON files."""
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config_path = config_path or os.getenv("CONFIG_PATH", "config.json")
        self.data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file, falling back to defaults if missing or invalid."""
        config = DEFAULT_CONFIG.copy()
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    file_config = json.load(f)
                    config.update(file_config)
                    self._validate_config(config)
        except (json.JSONDecodeError, IOError, ValueError) as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
            print("Using default configuration instead.")
            config = DEFAULT_CONFIG.copy()
        
        config = self._apply_env_overrides(config)
        return config
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration."""
        for key in config:
            env_key = f"{ENV_PREFIX}{key.upper()}"
            env_value = os.getenv(env_key)
            
            if env_value is not None:
                config[key] = self._convert_value(env_value, type(config[key]))
        
        self._validate_config(config)
        return config
    
    def _convert_value(self, value: str, target_type: type) -> Any:
        """Convert a string environment variable to the target type."""
        if target_type is bool:
            return value.lower() in ("true", "1", "yes", "on")
        elif target_type is int:
            return int(value)
        elif target_type is float:
            return float(value)
        else:
            return value
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate configuration values."""
        port = config.get("port")
        
        if not isinstance(port, int):
            raise ValueError(f"Port must be an integer, got {type(port).__name__}")
        
        if not (1024 <= port <= 65535):
            raise ValueError(f"Port must be between 1024 and 65535, got {port}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key with optional default."""
        return self.data.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        """Enable dictionary-style access to configuration values."""
        return self.data[key]
    
    def __contains__(self, key: str) -> bool:
        """Check if a configuration key exists."""
        return key in self.data
```
