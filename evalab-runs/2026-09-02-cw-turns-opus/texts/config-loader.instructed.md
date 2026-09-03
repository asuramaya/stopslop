```python
"""Load application settings from a JSON file, falling back to built-in defaults."""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

MIN_PORT = 1024
MAX_PORT = 65535
ENV_PREFIX = "APP_"

DEFAULT_SETTINGS = {
    "host": "127.0.0.1",
    "port": 8080,
    "log_level": "INFO",
    "max_connections": 100,
    "request_timeout_seconds": 30,
}

TRUE_WORDS = {"1", "true", "yes", "on"}
FALSE_WORDS = {"0", "false", "no", "off"}


class ConfigError(Exception):
    """Raised when a config file exists but cannot be read or validated."""


def _check_port(value):
    """Return None if `value` is a usable port, else a message explaining why not."""
    if isinstance(value, bool) or not isinstance(value, int):
        return f"port must be an integer, got {type(value).__name__}"
    if not MIN_PORT <= value <= MAX_PORT:
        return f"port must be between {MIN_PORT} and {MAX_PORT}, got {value}"
    return None


def _coerce(text, like):
    """Parse `text` into the type of `like`, the default for that key.

    Raises ValueError if the text does not fit that type.
    """
    if isinstance(like, bool):
        lowered = text.strip().lower()
        if lowered in TRUE_WORDS:
            return True
        if lowered in FALSE_WORDS:
            return False
        raise ValueError(f"expected a boolean, got {text!r}")
    if isinstance(like, int):
        return int(text.strip())
    if isinstance(like, float):
        return float(text.strip())
    return text


def env_overrides(environ=None, strict=False):
    """Return the settings named by `APP_<KEY>` variables, parsed to the default's type.

    Keys outside DEFAULT_SETTINGS are ignored with a warning. A value that does
    not parse is skipped, unless `strict` is set, in which case ConfigError is raised.
    """
    environ = os.environ if environ is None else environ
    overrides = {}

    for name, text in environ.items():
        if not name.startswith(ENV_PREFIX):
            continue
        key = name[len(ENV_PREFIX):].lower()
        if key not in DEFAULT_SETTINGS:
            logger.warning("Ignoring %s: no setting named %r", name, key)
            continue
        try:
            overrides[key] = _coerce(text, DEFAULT_SETTINGS[key])
        except ValueError as exc:
            if strict:
                raise ConfigError(f"{name}: {exc}") from exc
            logger.warning("Ignoring %s (%s)", name, exc)

    return overrides


def load_config(path, strict=False, environ=None):
    """Return settings from the JSON file at `path`, merged over the defaults.

    Environment variables named `APP_<KEY>` win over the file, which wins over
    the defaults. Unparseable JSON never propagates: the failure is logged and
    the defaults are used, whatever `strict` says. A missing file also yields the
    defaults. An unreadable file, a non-object file, or an out-of-range `port`
    yields the defaults unless `strict` is set, in which case ConfigError is raised.
    """
    path = Path(path)
    settings = dict(DEFAULT_SETTINGS)
    loaded = {}

    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.info("No config at %s; using defaults", path)
        raw = None
    except OSError as exc:
        if strict:
            raise ConfigError(f"cannot read {path}: {exc}") from exc
        logger.warning("Cannot read %s (%s); using defaults", path, exc)
        raw = None

    if raw is not None:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning(
                "Invalid JSON in %s at line %d column %d (%s); falling back to defaults",
                path, exc.lineno, exc.colno, exc.msg,
            )
            parsed = {}

        if not isinstance(parsed, dict):
            if strict:
                raise ConfigError(f"{path} must contain a JSON object")
            logger.warning("%s is not a JSON object; using defaults", path)
        else:
            unknown = set(parsed) - set(DEFAULT_SETTINGS)
            if unknown:
                logger.warning(
                    "Ignoring unknown keys in %s: %s", path, ", ".join(sorted(unknown))
                )
            loaded = {k: v for k, v in parsed.items() if k in DEFAULT_SETTINGS}

    loaded.update(env_overrides(environ, strict=strict))

    if "port" in loaded:
        problem = _check_port(loaded["port"])
        if problem:
            if strict:
                raise ConfigError(f"{problem} (from {path} or {ENV_PREFIX}PORT)")
            logger.warning("%s; using port %d", problem, settings["port"])
            del loaded["port"]

    settings.update(loaded)
    return settings
```
