```python
def validate(data, schema, *, allow_extra=False):
    """Check data against {key: type}, collecting every problem.

    Returns a list of human-readable strings, empty when data is valid.
    Nested schemas are supported: a dict value in `schema` is applied
    recursively to the corresponding dict in `data`.
    """
    if not isinstance(data, dict):
        return [f"expected a dict, got {type(data).__name__}"]

    errors = []

    for key, expected in schema.items():
        if key not in data:
            errors.append(f"{key}: missing")
            continue

        value = data[key]

        if isinstance(expected, dict):
            if not isinstance(value, dict):
                errors.append(
                    f"{key}: expected dict, got {type(value).__name__}"
                )
                continue
            errors.extend(
                f"{key}.{nested}"
                for nested in validate(value, expected, allow_extra=allow_extra)
            )
            continue

        # bool is a subclass of int, so isinstance(True, int) is True
        if expected is int and isinstance(value, bool):
            errors.append(f"{key}: expected int, got bool")
            continue

        if not isinstance(value, expected):
            name = getattr(expected, "__name__", str(expected))
            errors.append(
                f"{key}: expected {name}, got {type(value).__name__}"
            )

    if not allow_extra:
        for key in data:
            if key not in schema:
                errors.append(f"{key}: unexpected key")

    return errors
```
