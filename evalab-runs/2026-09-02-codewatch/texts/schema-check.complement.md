```python
def validate_schema(data, schema, required=None):
    """Check data against {key: type}, collecting all problems.

    Returns a list of human-readable problem strings, empty if data is valid.
    Keys in `required` (default: every key in the schema) must be present;
    other schema keys are optional but type-checked when present. Keys not
    in the schema are reported as unexpected.
    """
    if required is None:
        required = set(schema)
    else:
        required = set(required)

    unknown_required = required - set(schema)
    if unknown_required:
        raise ValueError(
            "required names keys absent from schema: "
            + ", ".join(sorted(unknown_required))
        )

    if not isinstance(data, dict):
        return ["top level: expected dict, got %s" % type(data).__name__]

    problems = []

    for key in sorted(required):
        if key not in data:
            problems.append("%s: missing (expected %s)" % (key, _name(schema[key])))

    for key in sorted(data):
        if key not in schema:
            problems.append("%s: unexpected key" % key)
            continue
        expected = schema[key]
        value = data[key]
        # bool is a subclass of int, so an int field would silently accept True
        if expected is int and isinstance(value, bool):
            problems.append("%s: expected int, got bool" % key)
        elif not isinstance(value, expected):
            problems.append(
                "%s: expected %s, got %s" % (key, _name(expected), type(value).__name__)
            )

    return problems


def _name(expected):
    if isinstance(expected, tuple):
        return " or ".join(t.__name__ for t in expected)
    return expected.__name__
```
