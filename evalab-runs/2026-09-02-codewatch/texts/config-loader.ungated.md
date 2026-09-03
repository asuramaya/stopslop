`config_loader.py` (57 lines). Ran through the cases above — missing file, valid override, non-int port, out-of-range port, bool port, malformed JSON — all behaved as intended.

Design notes:
- Defaults are copied and the file's keys merged over them, so a partial config file works.
- `ConfigError` subclasses `ValueError`, so callers that already catch `ValueError` keep working.
- A missing file is the only silent fallback. An unreadable file (permissions, is-a-directory) raises rather than pretending it's absent — that's usually a real misconfiguration.
- `port` validation rejects `bool` explicitly, since `True` is an `int` in Python and would otherwise fail only on the range check.
- Validation runs on the merged value, so the default port is checked too.
