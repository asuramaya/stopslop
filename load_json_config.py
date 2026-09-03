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
    """The config file exists but cannot be used as config."""


PORT_MIN, PORT_MAX = 1024, 65535

ENV_PREFIX = "APP_"

TRUE_WORDS = {"1", "true", "yes", "on"}
FALSE_WORDS = {"0", "false", "no", "off"}


def _coerce(raw, current, name):
    """Read the string `raw` as the type `current` already holds.

    A key with no value yet has no type to match, so its value is read as
    JSON when that parses and kept as a string when it does not.
    """
    if isinstance(current, bool):
        word = raw.strip().lower()
        if word in TRUE_WORDS:
            return True
        if word in FALSE_WORDS:
            return False
        raise ConfigError(f"{name}: expected a boolean, got {raw!r}")
    if isinstance(current, (int, float)):
        try:
            return type(current)(raw)
        except ValueError as exc:
            raise ConfigError(
                f"{name}: expected {type(current).__name__}, got {raw!r}"
            ) from exc
    if isinstance(current, str):
        return raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _apply_env(config, prefix, environ):
    """Overlay every `prefix`-named variable onto `config`, in place.

    Returns the set of keys the environment touched.
    """
    touched = set()
    for name, raw in sorted(environ.items()):
        if not name.startswith(prefix):
            continue
        key = name[len(prefix):].lower()
        if not key:
            continue
        config[key] = _coerce(raw, config.get(key), name)
        log.debug("%s overrides %s", name, key)
        touched.add(key)
    return touched


def _check_port(config, source):
    """Raise ConfigError unless config["port"] is an int in the legal range."""
    port = config.get("port")
    if port is None:
        return
    if isinstance(port, bool) or not isinstance(port, int):
        raise ConfigError(f"{source}: port must be an integer, got {port!r}")
    if not PORT_MIN <= port <= PORT_MAX:
        raise ConfigError(
            f"{source}: port must be between {PORT_MIN} and {PORT_MAX}, got {port}"
        )


def _finish(config, source, env_prefix, environ):
    """Overlay the environment, then validate what the caller will get."""
    if env_prefix is not None:
        touched = _apply_env(
            config, env_prefix, os.environ if environ is None else environ
        )
        if "port" in touched:
            source = f"{env_prefix}PORT"
    _check_port(config, source)
    return config


def load(path, defaults=None, env_prefix=ENV_PREFIX, environ=None):
    """Return `defaults` merged with the JSON object at `path`.

    A missing file gives back the defaults alone, logged at INFO. So does
    a file that exists but cannot be parsed as a JSON object -- bad JSON,
    or a top level that is not an object -- logged at WARNING so the
    broken file leaves a trace instead of taking the process down. A file
    that cannot be read at all still raises ConfigError.

    Any variable named `env_prefix` plus an upper-cased key overrides that
    key, whatever the file said: APP_PORT=9000 sets `port` to 9000. The
    string is read as the type the key already holds, so `port` stays an
    int and `debug` takes true/false/yes/no/on/off/1/0. A name the config
    has no value for is read as JSON, or kept as a string when that fails.
    Pass env_prefix=None to ignore the environment, or `environ` to read a
    dict instead of os.environ.

    A `port` key in the result must be an integer between 1024 and 65535;
    anything else raises ConfigError.

    The merge is one level deep: a nested object in the file replaces the
    default wholesale rather than being merged key by key.
    """
    if env_prefix == "":
        raise ValueError("env_prefix must be non-empty, or None to disable")
    config = dict(DEFAULTS if defaults is None else defaults)
    path = Path(path)

    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        log.info("no config at %s; using defaults", path)
        return _finish(config, "defaults", env_prefix, environ)
    except OSError as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        log.warning("%s is not valid JSON (%s); using defaults", path, exc)
        return _finish(config, "defaults", env_prefix, environ)

    if not isinstance(parsed, dict):
        log.warning(
            "%s must hold a JSON object, got %s; using defaults",
            path,
            type(parsed).__name__,
        )
        return _finish(config, "defaults", env_prefix, environ)

    config.update(parsed)
    return _finish(config, str(path), env_prefix, environ)
