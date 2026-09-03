"""Load and validate a JSON configuration file."""

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

MIN_PORT = 1024
MAX_PORT = 65535

DEFAULTS = {
    "host": "127.0.0.1",
    "port": 8080,
    "debug": False,
}


class ConfigError(ValueError):
    """The config file exists but its contents are unusable."""


def default_config():
    return dict(DEFAULTS)


def validate_port(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"port must be an integer, got {type(value).__name__}")
    if not MIN_PORT <= value <= MAX_PORT:
        raise ConfigError(f"port {value} is outside {MIN_PORT}-{MAX_PORT}")
    return value


def load_config(path, defaults=None):
    """Read `path` and merge it over the defaults.

    A missing file yields the defaults untouched. Malformed JSON, a
    non-object top level, or a bad `port` raises ConfigError.
    """
    config = default_config() if defaults is None else dict(defaults)
    path = Path(path)

    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        log.info("no config at %s; using defaults", path)
        return config

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{path} is not valid JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ConfigError(f"{path} must hold a JSON object, got {type(parsed).__name__}")

    config.update(parsed)
    if "port" not in config:
        raise ConfigError(f"{path} has no port and no default supplies one")
    validate_port(config["port"])
    return config
