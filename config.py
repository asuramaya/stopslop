"""Load a JSON config file, falling back to defaults when it is missing."""

import json
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

DEFAULTS = {
    "host": "127.0.0.1",
    "port": 8080,
    "debug": False,
}


class ConfigError(ValueError):
    """The config file exists but its contents are not usable."""


def load(path, defaults=None):
    """Return `defaults` merged with the JSON object stored at `path`.

    A file that is not there gives back a copy of the defaults alone,
    logged at INFO. A file that is there but holds bad JSON also falls
    back to the defaults, logged at WARNING. A file whose top level is
    not an object raises ConfigError.

    The merge is one level deep: a nested object in the file replaces
    the matching default outright instead of merging key by key.

    After the merge, any key also set as an environment variable
    `CONFIG_<KEY>` (upper-cased) is overridden by that variable's value.
    The raw string is parsed as JSON so ints/bools/etc. come through as
    the right type; if that parse fails, the raw string is used as-is.

    `port`, whether it came from the file, the environment, or the
    defaults, must be an integer between 1024 and 65535; otherwise
    ConfigError is raised.
    """
    config = dict(DEFAULTS if defaults is None else defaults)
    path = Path(path)

    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        log.info("no config at %s; using defaults", path)
        raw = None
    except OSError as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc

    if raw is not None:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            log.warning("%s is not valid JSON (%s); using defaults", path, exc)
            parsed = None

        if parsed is not None:
            if not isinstance(parsed, dict):
                raise ConfigError(
                    f"{path} must hold a JSON object, got {type(parsed).__name__}"
                )
            config.update(parsed)

    for key in config:
        env_name = f"CONFIG_{key.upper()}"
        if env_name not in os.environ:
            continue
        raw_value = os.environ[env_name]
        try:
            config[key] = json.loads(raw_value)
        except json.JSONDecodeError:
            config[key] = raw_value

    port = config.get("port")
    if not isinstance(port, int) or isinstance(port, bool) or not (1024 <= port <= 65535):
        raise ConfigError(f"port must be an integer between 1024 and 65535, got {port!r}")

    return config
