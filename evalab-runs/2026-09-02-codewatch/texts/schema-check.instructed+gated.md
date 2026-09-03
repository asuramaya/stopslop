```python
from typing import Any


class SchemaError(Exception):
    """Raised when a payload does not match its schema."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("; ".join(problems))


def validate(payload: dict[str, Any], schema: dict[str, type],
             allow_extra: bool = False) -> list[str]:
    """Check payload against a {key: type} schema.

    Returns every problem found, as a list of human-readable strings.
    An empty list means the payload is valid. Extra keys are reported
    unless allow_extra is set.
    """
    if not isinstance(payload, dict):
        return [f"payload is {type(payload).__name__}, expected dict"]

    problems = []

    for key, expected in schema.items():
        if key not in payload:
            problems.append(f"missing key {key!r} (expected {expected.__name__})")
            continue

        value = payload[key]
        # bool is a subclass of int, so an isinstance check alone would let
        # True through wherever an int is wanted.
        if expected is int and isinstance(value, bool):
            problems.append(f"{key!r}: got bool, expected int")
        elif not isinstance(value, expected):
            problems.append(
                f"{key!r}: got {type(value).__name__}, expected {expected.__name__}"
            )

    if not allow_extra:
        for key in payload.keys() - schema.keys():
            problems.append(f"unexpected key {key!r}")

    return problems


def validate_or_raise(payload: dict[str, Any], schema: dict[str, type],
                      allow_extra: bool = False) -> None:
    problems = validate(payload, schema, allow_extra)
    if problems:
        raise SchemaError(problems)
```
