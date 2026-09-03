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
    """The config file exists but its contents are unusable."""


PORT_MIN = 1024
PORT_MAX = 65535

ENV_PREFIX = "APP_"

TRUE_WORDS = {"1", "true", "yes", "on"}
FALSE_WORDS = {"0", "false", "no", "off"}


def _coerce(raw, current, name):
    """Read the string `raw` as the type `current` already has.

    A key the config does not carry yet has no type to match, so its value
    is read as JSON when that parses and left as a string when it does not.
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
    """Reject a `port` that is not an integer in the unprivileged range."""
    port = config.get("port")
    if isinstance(port, bool) or not isinstance(port, int):
        raise ConfigError(f"{source}: port must be an integer, got {port!r}")
    if not PORT_MIN <= port <= PORT_MAX:
        raise ConfigError(f"{source}: port {port} is outside {PORT_MIN}-{PORT_MAX}")


def load(path, defaults=None, env_prefix=ENV_PREFIX, environ=None):
    """Return the defaults merged with whatever `path` holds.

    A missing file gives back the defaults alone, and so does a file that
    is unreadable as config: bad JSON, or a top level that is not an
    object. Both are logged at WARNING with the parser's complaint, so a
    fallback leaves a trace naming the file. An unreadable *file* (bad
    permissions, a directory in the path) still raises ConfigError, since
    that is a broken deployment rather than a broken config. A `port` key
    must be an integer between PORT_MIN and PORT_MAX.

    Any variable named `env_prefix` plus an upper-case key overrides that
    key, whatever the file said: APP_PORT=9000 sets `port` to 9000. The
    value is read as the type the key already holds, so `port` stays an
    int and `debug` takes true/false/yes/no/on/off/1/0. Pass
    env_prefix=None to ignore the environment.
    """
    config = dict(DEFAULTS if defaults is None else defaults)
    path = Path(path)
    if env_prefix == "":
        raise ValueError("env_prefix must be non-empty, or None to disable")

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


def save(path, config):
    """Write `config` to `path`, creating parent directories as needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return path
