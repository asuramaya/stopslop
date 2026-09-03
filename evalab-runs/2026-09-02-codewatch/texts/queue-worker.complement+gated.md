```python
import logging
import queue
import threading

logger = logging.getLogger(__name__)

_SENTINEL = object()


class QueueWorker:
    """Runs `callback` against every item put on the queue, on one background thread."""

    def __init__(self, callback, maxsize=0, name="queue-worker"):
        self._callback = callback
        self._queue = queue.Queue(maxsize=maxsize)
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._started = False

    def start(self):
        if self._started:
            raise RuntimeError("worker already started")
        self._started = True
        self._thread.start()

    def submit(self, item):
        self._queue.put(item)

    def _run(self):
        while True:
            item = self._queue.get()
            if item is _SENTINEL:
                self._queue.task_done()
                return
            try:
                self._callback(item)
            except Exception:
                # One bad item must not kill the thread; the queue would then
                # fill and every submit() would block forever.
                logger.exception("callback failed for item %r", item)
            finally:
                self._queue.task_done()

    def stop(self, timeout=None):
        """Drain what is already queued, then join the thread."""
        if not self._started:
            return
        self._queue.put(_SENTINEL)
        self._thread.join(timeout)
        if self._thread.is_alive():
            raise TimeoutError("worker did not shut down within %s seconds" % timeout)
        self._started = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()
        return False
```
