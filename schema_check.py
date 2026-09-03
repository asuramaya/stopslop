"""Check a dict against a {key: type} schema, collecting every problem."""

from typing import Any


def check_schema(
    data: dict[str, Any],
    schema: dict[str, type | tuple[type, ...]],
    allow_extra: bool = True,
) -> list[str]:
    """Compare `data` against `schema` and return every mismatch found.

    Checking continues past the first failure, so one call reports all of
    the missing keys, all of the wrong types, and (when `allow_extra` is
    false) all of the unexpected keys. An empty list means `data` matches.

    A bool is not accepted where an int is required, even though bool is a
    subclass of int, because a flag arriving in a count field is almost
    always the bug the caller is looking for.

    Args:
        data: The mapping to check.
        schema: Required key mapped to its allowed type, or to a tuple of
            allowed types as `isinstance` accepts.
        allow_extra: If false, keys in `data` but not in `schema` are
            reported as problems.

    Returns:
        Problem descriptions, one per key, ordered by schema key and then
        by extra key. Both orderings follow insertion order.

    Raises:
        TypeError: `data` is not a dict.
    """
    if not isinstance(data, dict):
        raise TypeError(f"data must be a dict, got {type(data).__name__}")

    problems = []
    for key, expected in schema.items():
        if key not in data:
            problems.append(f"{key}: missing, expected {_name(expected)}")
            continue
        value = data[key]
        allowed = expected if isinstance(expected, tuple) else (expected,)
        if isinstance(value, bool) and bool not in allowed and int in allowed:
            problems.append(f"{key}: expected {_name(expected)}, got bool")
        elif not isinstance(value, allowed):
            problems.append(
                f"{key}: expected {_name(expected)}, got {type(value).__name__}"
            )

    if not allow_extra:
        for key in data:
            if key not in schema:
                problems.append(f"{key}: unexpected key")

    return problems


def _name(expected: type | tuple[type, ...]) -> str:
    """Render one type or a tuple of types the way an error message reads."""
    if isinstance(expected, tuple):
        return " or ".join(t.__name__ for t in expected)
    return expected.__name__
