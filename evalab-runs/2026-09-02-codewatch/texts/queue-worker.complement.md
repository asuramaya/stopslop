```python
import logging
import queue
import threading

log = logging.getLogger(__name__)

_SENTINEL = object()


class Worker:
    """Consumes items from a queue on a background thread."""

    def __init__(self, callback, maxsize=0, name="worker"):
        self._callback = callback
        self._queue = queue.Queue(maxsize=maxsize)
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._started = False

    def start(self):
        if self._started:
            raise RuntimeError("worker already started")
        self._started = True
        self._thread.start()
        return self

    def submit(self, item, timeout=None):
        if item is _SENTINEL:
            raise ValueError("cannot submit the shutdown sentinel as an item")
        self._queue.put(item, timeout=timeout)

    def _run(self):
        while True:
            item = self._queue.get()
            try:
                if item is _SENTINEL:
                    return
                self._callback(item)
            except Exception:
                # One bad item must not kill the thread and strand the queue.
                log.exception("worker callback failed on %r", item)
            finally:
                self._queue.task_done()

    def join_queue(self):
        """Block until every submitted item has been processed."""
        self._queue.join()

    def stop(self, timeout=None):
        if not self._started:
            return
        self._queue.put(_SENTINEL)
        self._thread.join(timeout)
        if self._thread.is_alive():
            log.warning("worker thread did not exit within %s seconds", timeout)

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc, tb):
        self.stop()
```
