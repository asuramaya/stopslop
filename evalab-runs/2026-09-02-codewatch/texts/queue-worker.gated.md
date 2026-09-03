```python
import queue
import threading


_SENTINEL = object()


class Worker:
    """Runs a callback over items pulled from a queue on a background thread."""

    def __init__(self, callback, on_error=None, maxsize=0, name="worker"):
        self.callback = callback
        self.on_error = on_error
        self.queue = queue.Queue(maxsize=maxsize)
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._started = False

    def start(self):
        if self._started:
            raise RuntimeError("worker already started")
        self._started = True
        self._thread.start()
        return self

    def submit(self, item):
        if item is _SENTINEL:
            raise ValueError("cannot submit the sentinel")
        self.queue.put(item)

    def _run(self):
        while True:
            item = self.queue.get()
            try:
                if item is _SENTINEL:
                    return
                self.callback(item)
            except Exception as exc:
                if self.on_error is None:
                    raise
                self.on_error(item, exc)
            finally:
                self.queue.task_done()

    def stop(self, drain=True, timeout=None):
        """Queue the sentinel and wait for the thread to finish."""
        if not self._started:
            return
        if drain:
            self.queue.join()
        self.queue.put(_SENTINEL)
        self._thread.join(timeout)

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc_info):
        self.stop()
        return False
```

Notes on the choices:

- The sentinel is a module-private `object()`, not `None` — `None` is a plausible payload, and an identity check on a unique object can't collide with real work.
- `stop(drain=True)` waits for already-queued items via `queue.join()` before the sentinel goes in, so nothing submitted before the shutdown gets dropped. `drain=False` puts the sentinel behind whatever is queued anyway, so it still finishes the backlog; the difference is only whether *stop* blocks on it. If you want true abandon-the-backlog behavior, you need a separate `threading.Event` the loop checks.
- `task_done()` sits in `finally` so a raising callback can't wedge `queue.join()` forever.
- With no `on_error`, an exception kills the thread — loud failure rather than a worker that silently stopped consuming. Pass `on_error` for the log-and-continue behavior.
- The thread is a daemon so a forgotten `stop()` doesn't hang interpreter exit, but `stop()` is still the correct path — daemon threads are killed mid-item at shutdown.

Usage:

```python
with Worker(print, on_error=lambda item, e: print("failed", item, e)) as w:
    for i in range(5):
        w.submit(i)
```
