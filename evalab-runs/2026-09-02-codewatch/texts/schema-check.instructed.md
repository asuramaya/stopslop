```python
def validate(record, schema, allow_extra=False):
    """Check a dict against a {key: type} schema.

    Returns a list of human-readable problems, empty if the record is valid.
    Every key is checked, so one call surfaces all the errors at once rather
    than stopping at the first bad field.

    A type may be a tuple of types, exactly as isinstance accepts. Optional
    fields are declared by including type(None) in that tuple.
    """
    if not isinstance(record, dict):
        return [f"expected a dict, got {type(record).__name__}"]

    problems = []

    for key, expected in schema.items():
        if key not in record:
            problems.append(f"{key}: missing")
            continue

        value = record[key]
        if not isinstance(expected, tuple):
            expected = (expected,)

        if not isinstance(value, expected):
            names = " or ".join(t.__name__ for t in expected)
            problems.append(
                f"{key}: expected {names}, got {type(value).__name__}"
            )
        elif bool not in expected and isinstance(value, bool):
            # bool subclasses int, so an int field silently accepts True.
            names = " or ".join(t.__name__ for t in expected)
            problems.append(f"{key}: expected {names}, got bool")

    if not allow_extra:
        for key in record:
            if key not in schema:
                problems.append(f"{key}: not in schema")

    return problems
```
