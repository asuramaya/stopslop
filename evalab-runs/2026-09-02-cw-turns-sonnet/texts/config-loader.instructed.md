```python
def load_config(path):
    config_path = Path(path)

    if not config_path.exists():
        logger.warning("Config file %s not found; using defaults", config_path)
        config = dict(DEFAULT_CONFIG)
    else:
        try:
            with config_path.open("r") as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            logger.warning(
                "Config file %s is not valid JSON (%s); using defaults", config_path, exc
            )
            data = {}
        config = dict(DEFAULT_CONFIG)
        config.update(data)

    apply_env_overrides(config)
    validate_config(config)
    return config


def apply_env_overrides(config):
    for key in config:
        env_var = f"CONFIG_{key.upper()}"
        if env_var not in os.environ:
            continue
        raw_value = os.environ[env_var]
        default_value = config[key]
        if isinstance(default_value, bool):
            config[key] = raw_value.lower() in ("1", "true", "yes", "on")
        elif isinstance(default_value, int):
            config[key] = int(raw_value)
        else:
            config[key] = raw_value


def validate_config(config):
    port = config.get("port")
    if not isinstance(port, int) or isinstance(port, bool):
        raise ValueError(f"port must be an integer, got {port!r}")
    if port < 1024 or port > 65535:
        raise ValueError(f"port must be between 1024 and 65535, got {port}")
```
