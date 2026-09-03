`retry.py` — 58 lines. It succeeded on attempt 3 in the smoke test, and the `attempts=0` guard fires.

```python
def retry(attempts=3, delay=1.0, backoff=2.0, max_delay=None, jitter=False,
          exceptions=(Exception,)):
```

Details worth knowing:

- The delay is per-wrapper-call, not per-decorator, so a reused wrapper always starts back at `delay`.
- `exceptions` defaults to everything; narrow it in real use, otherwise a `TypeError` from a bad argument gets retried three times before it surfaces.
- The last attempt re-raises with `raise` bare, so the original traceback survives.
- `jitter` scales downward only (factor in [0.5, 1.0]), which keeps the schedule an upper bound while still de-synchronizing concurrent callers.
- Failures log at WARNING with `exc_info` — that's the traceback you see in the test output above, not a crash.

It's sync-only. An async function wrapped by this returns its coroutine without awaiting it, so a failure never reaches the `except`; that needs a separate `async def` wrapper branch if you want it.
