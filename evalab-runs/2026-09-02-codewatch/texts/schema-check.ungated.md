`schema_check.py:6` — `check_schema(data, schema, allow_extra=True)` returns a list of problem strings, empty when the dict matches.

```python
s = {"name": str, "age": int, "tags": (list, tuple)}
check_schema({"age": True, "tags": "x", "z": 1}, s, allow_extra=False)
# ['name: missing, expected str',
#  'age: expected int, got bool',
#  'tags: expected list or tuple, got str',
#  'z: unexpected key']
```

Two judgment calls worth knowing about:

- A schema value can be a tuple of types, passed straight to `isinstance`, so optional shapes like `(list, tuple)` or `(int, float)` work without extra machinery.
- `True` is rejected where `int` is required. Python says `isinstance(True, int)` is true, but a flag landing in a count field is usually the bug you were looking for. If you want the permissive behaviour, write `(int, bool)` in the schema.

It does not recurse into nested dicts — the schema is flat by design, per your "simple schema" framing. Say the word if you want nested dicts to accept a sub-schema as their value.
