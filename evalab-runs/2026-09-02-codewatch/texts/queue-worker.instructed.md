```python
import logging
import queue
import threading

logger = logging.getLogger(__name__)

_SHUTDOWN = object()


class QueueWorker:
    """Runs a callback against items from a queue on a single background thread."""

    def __init__(self, handle_item, name="queue-worker", max_pending=0):
        self.handle_item = handle_item
        self.items = queue.Queue(maxsize=max_pending)
        self.thread = threading.Thread(target=self._drain, name=name, daemon=True)
        self._started = False

    def start(self):
        if self._started:
            raise RuntimeError("worker already started")
        self._started = True
        self.thread.start()
        return self

    def submit(self, item):
        if item is _SHUTDOWN:
            raise ValueError("cannot submit the shutdown sentinel")
        self.items.put(item)

    def _drain(self):
        while True:
            item = self.items.get()
            try:
                if item is _SHUTDOWN:
                    return
                self.handle_item(item)
            except Exception:
                logger.exception("worker callback failed on %r", item)
            finally:
                self.items.task_done()

    def stop(self, timeout=None, drain=True):
        """Ask the thread to finish. With drain, queued items run before the sentinel."""
        if not self._started:
            return
        if drain:
            self.items.join()
        self.items.put(_SHUTDOWN)
        self.thread.join(timeout)
        if self.thread.is_alive():
            logger.warning("worker %s did not exit within %ss", self.thread.name, timeout)

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc, tb):
        self.stop(drain=exc_type is None)
        return False
```
