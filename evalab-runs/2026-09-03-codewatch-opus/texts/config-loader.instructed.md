```python
"""Load application config from JSON, with defaults and environment overrides."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Mapping

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path("~/.config/myapp/config.json").expanduser()

ENV_PREFIX = "MYAPP_"

MIN_PORT = 1024
MAX_PORT = 65535

DEFAULTS: dict[str, Any] = {
    "host": "127.0.0.1",
    "port": 8080,
    "log_level": "INFO",
    "timeout_seconds": 30,
    "retries": 3,
}


class ConfigError(Exception):
    """Raised when a config file is present and readable but fails validation."""


def _merge(defaults: Mapping[str, Any], overrides: Mapping[str, Any]) -> dict[str, Any]:
    merged = dict(defaults)
    for key, value in overrides.items():
        existing = merged.get(key)
        if isinstance(existing, Mapping) and isinstance(value, Mapping):
            merged[key] = _merge(existing, value)
        else:
            merged[key] = value
    return merged


def _coerce(text: str, current: Any) -> Any:
    """Parse an env var string to match the type of the value it replaces."""
    if isinstance(current, bool):
        lowered = text.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
        return text
    if isinstance(current, int):
        try:
            return int(text)
        except ValueError:
            return text
    if isinstance(current, float):
        try:
            return float(text)
        except ValueError:
            return text
    if isinstance(current, (Mapping, list)):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    return text


def _apply_env_overrides(config: Mapping[str, Any], environ: Mapping[str, str]) -> dict[str, Any]:
    """Override any top-level key from {ENV_PREFIX}{KEY.upper()}."""
    overridden = dict(config)
    for key in config:
        env_name = f"{ENV_PREFIX}{key.upper()}"
        if env_name in environ:
            overridden[key] = _coerce(environ[env_name], config[key])
            logger.debug("Overrode %s from %s", key, env_name)
    return overridden


def _validate_port(port: Any, source: str) -> None:
    # bool is an int subclass, and `"port": true` is a mistake worth catching.
    if isinstance(port, bool) or not isinstance(port, int):
        raise ConfigError(f"port from {source} must be an integer, got {type(port).__name__}")
    if not MIN_PORT <= port <= MAX_PORT:
        raise ConfigError(f"port from {source} must be between {MIN_PORT} and {MAX_PORT}, got {port}")


def _read_file_config(config_path: Path) -> dict[str, Any] | None:
    """Return the parsed JSON object at `config_path`, or None if unusable."""
    try:
        raw = config_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.info("No config at %s; using defaults", config_path)
        return None
    except OSError as exc:
        logger.warning("Cannot read config at %s (%s); using defaults", config_path, exc)
        return None

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("Invalid JSON in %s (%s); using defaults", config_path, exc)
        return None

    if not isinstance(parsed, dict):
        logger.warning(
            "Config in %s is %s, not a JSON object; using defaults",
            config_path,
            type(parsed).__name__,
        )
        return None

    logger.debug("Loaded config from %s", config_path)
    return parsed


def load_config(
    path: str | os.PathLike[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Return DEFAULTS, overlaid with the config file, overlaid with the environment.

    Any top-level key can be set from `{ENV_PREFIX}{KEY.upper()}`; the string is
    coerced to the type of the value it replaces, so MYAPP_PORT=9000 stays an int.
    A missing, unreadable, or malformed file yields the defaults unchanged, with a
    warning logged for anything worse than absence. Values that are present but
    invalid — a port outside the allowed range — raise ConfigError, since the
    caller asked for that setting and got it wrong.
    """
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH

    config = dict(DEFAULTS)
    from_file = _read_file_config(config_path)
    if from_file is not None:
        config = _merge(config, from_file)

    port_source = str(config_path) if from_file is not None else "defaults"
    env = os.environ if environ is None else environ
    port_env_name = f"{ENV_PREFIX}PORT"
    config = _apply_env_overrides(config, env)
    if port_env_name in env:
        port_source = port_env_name

    _validate_port(config["port"], port_source)
    return config
```
