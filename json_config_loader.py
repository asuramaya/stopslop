"""Load a JSON config file from disk, falling back to defaults if missing."""

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

DEFAULTS = {
    "host": "127.0.0.1",
    "port": 8080,
    "debug": False,
}


class ConfigError(ValueError):
    """The config file exists but its contents cannot be used."""


def load_config(path, defaults=None):
    """Load JSON config from `path`, merged over `defaults`.

    Missing file: return a copy of the defaults.
    Invalid JSON: return a copy of the defaults.
    Valid JSON whose top level is not an object: raise ConfigError.
    """
    merged = dict(DEFAULTS if defaults is None else defaults)
    path = Path(path)

    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        log.info("no config file at %s, using defaults", path)
        return merged
    except OSError as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        log.warning("%s is not valid JSON (%s), using defaults", path, exc)
        return merged

    if not isinstance(parsed, dict):
        raise ConfigError(f"{path} must contain a JSON object at the top level")

    merged.update(parsed)
    return merged


if __name__ == "__main__":
    import sys

    print(json.dumps(load_config(sys.argv[1] if len(sys.argv) > 1 else "config.json"), indent=2))
