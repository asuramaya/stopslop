```python
def validate(data, schema, *, allow_extra=True):
    """Check `data` against a {key: type} schema, collecting every problem.

    Returns a list of human-readable error strings, empty if the data is
    valid. Nested dicts are handled by giving a dict-valued schema entry.
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
            errors += [f"{key}.{e}" for e in validate(value, expected,
                                                      allow_extra=allow_extra)]
        elif not _matches(value, expected):
            errors.append(f"{key}: expected {_name(expected)}, "
                          f"got {type(value).__name__}")

    if not allow_extra:
        for key in data:
            if key not in schema:
                errors.append(f"{key}: unexpected key")
    return errors


def _matches(value, expected):
    # bool is a subclass of int, but an int field almost never wants True.
    if expected in (int, float) and isinstance(value, bool):
        return False
    return isinstance(value, expected)


def _name(expected):
    if isinstance(expected, tuple):
        return " or ".join(t.__name__ for t in expected)
    return expected.__name__
```

Three things beyond the bare ask, each cheap: a tuple of types works as a schema value (`isinstance` already accepts one), a dict value recurses and prefixes the child errors with `parent.child`, and `bool` is rejected for `int`/`float` fields since `isinstance(True, int)` is otherwise true.

Run against `{'name': str, 'age': int, 'score': (int, float), 'addr': {'city': str, 'zip': str}}`, a broken input gives all six problems at once:

```
['name: missing', 'age: expected int, got bool', 'score: expected int or float, got str',
 'addr.city: expected str, got int', 'addr.zip: missing', 'junk: unexpected key']
```

Note the recursion inherits `allow_extra` — if you want extras banned at the top level but tolerated inside nested objects, that flag needs to move into the schema itself.
