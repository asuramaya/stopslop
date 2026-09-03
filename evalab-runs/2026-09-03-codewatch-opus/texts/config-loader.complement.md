```python
"""Load a JSON config from disk, falling back to built-in defaults."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Mapping

logger = logging.getLogger(__name__)

MIN_PORT = 1024
MAX_PORT = 65535

ENV_PREFIX = "APP_"

DEFAULT_CONFIG: Dict[str, Any] = {
    "host": "127.0.0.1",
    "port": 8080,
    "workers": 4,
    "debug": False,
    "log_level": "INFO",
}


class ConfigError(Exception):
    """Raised when a config file exists but cannot be used."""


def _merge(defaults: Dict[str, Any], overrides: Mapping[str, Any]) -> Dict[str, Any]:
    merged = dict(defaults)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _coerce(raw: str, current: Any) -> Any:
    """Parse an env string into the type the existing value suggests.

    Environment variables are always strings, so a bare "8080" would shadow an
    int port with text and fail validation for the wrong reason.
    """
    if isinstance(current, bool):
        lowered = raw.strip().lower()
        if lowered in ("1", "true", "yes", "on"):
            return True
        if lowered in ("0", "false", "no", "off"):
            return False
        raise ConfigError(f"expected a boolean, got {raw!r}")
    if isinstance(current, int):
        try:
            return int(raw)
        except ValueError as exc:
            raise ConfigError(f"expected an integer, got {raw!r}") from exc
    if isinstance(current, float):
        try:
            return float(raw)
        except ValueError as exc:
            raise ConfigError(f"expected a number, got {raw!r}") from exc
    if isinstance(current, (dict, list)):
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ConfigError(f"expected JSON, got {raw!r}") from exc
    return raw


def _env_overrides(config: Mapping[str, Any], env: Mapping[str, str]) -> Dict[str, Any]:
    """Collect APP_<KEY> values for keys already present in `config`.

    Only known keys are honoured, so an unrelated APP_* variable in the
    environment cannot invent a setting the application never reads.
    """
    overrides: Dict[str, Any] = {}
    for key, current in config.items():
        name = ENV_PREFIX + key.upper()
        if name not in env:
            continue
        try:
            overrides[key] = _coerce(env[name], current)
        except ConfigError as exc:
            logger.warning("Ignoring %s: %s", name, exc)
    return overrides


def _validate_port(config: Mapping[str, Any], source: str) -> None:
    if "port" not in config:
        return

    port = config["port"]
    # bool is a subclass of int, and True would otherwise pass as port 1.
    if isinstance(port, bool) or not isinstance(port, int):
        raise ConfigError(f"{source}: port must be an integer, got {type(port).__name__}")
    if not MIN_PORT <= port <= MAX_PORT:
        raise ConfigError(f"{source}: port must be between {MIN_PORT} and {MAX_PORT}, got {port}")


def load_config(
    path: str | os.PathLike[str],
    defaults: Dict[str, Any] | None = None,
    env: Mapping[str, str] | None = None,
) -> Dict[str, Any]:
    """Return the config at `path` layered over `defaults`, then over the environment.

    Neither a missing file nor an unusable one is an error: the defaults are
    returned instead, with a warning for anything that looked like a real
    attempt at a config. Environment overrides still apply to that fallback,
    so `APP_PORT` works whether or not the file loaded. Only the defaults
    themselves must be valid.
    """
    base = DEFAULT_CONFIG if defaults is None else defaults
    environ = os.environ if env is None else env

    def fall_back(reason: str | None = None) -> Dict[str, Any]:
        if reason is not None:
            logger.warning("%s; falling back to defaults", reason)
        result = dict(base)
        _validate_port(result, "defaults")
        overridden = _merge(result, _env_overrides(result, environ))
        try:
            _validate_port(overridden, "environment")
        except ConfigError as exc:
            logger.warning("%s; ignoring environment override", exc)
            return result
        return overridden

    try:
        with open(path, encoding="utf-8") as handle:
            loaded = json.load(handle)
    except FileNotFoundError:
        logger.info("No config at %s; using defaults", path)
        return fall_back()
    except json.JSONDecodeError as exc:
        return fall_back(f"{path} is not valid JSON: {exc}")
    except OSError as exc:
        return fall_back(f"could not read {path}: {exc}")

    if not isinstance(loaded, dict):
        return fall_back(f"{path} must contain a JSON object, got {type(loaded).__name__}")

    merged = _merge(base, loaded)
    merged = _merge(merged, _env_overrides(merged, environ))
    try:
        _validate_port(merged, str(path))
    except ConfigError as exc:
        return fall_back(str(exc))
    return merged
```
