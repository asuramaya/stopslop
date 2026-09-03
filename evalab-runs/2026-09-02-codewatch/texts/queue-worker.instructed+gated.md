```python
import logging
import queue
import threading

log = logging.getLogger(__name__)

_SHUTDOWN = object()


class QueueWorker:
    """Consume items from a queue on a background thread until told to stop."""

    def __init__(self, handle_item, work_queue=None, name="queue-worker"):
        self.handle_item = handle_item
        self.queue = work_queue if work_queue is not None else queue.Queue()
        self.thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._started = False

    def start(self):
        if self._started:
            raise RuntimeError("worker already started")
        self._started = True
        self.thread.start()

    def submit(self, item):
        if item is _SHUTDOWN:
            raise ValueError("cannot submit the shutdown sentinel as an item")
        self.queue.put(item)

    def stop(self, timeout=None):
        """Drain whatever is queued, then join the thread."""
        self.queue.put(_SHUTDOWN)
        self.thread.join(timeout)
        if self.thread.is_alive():
            log.warning("worker thread did not exit within %s seconds", timeout)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()
        return False

    def _run(self):
        while True:
            item = self.queue.get()
            try:
                if item is _SHUTDOWN:
                    return
                self.handle_item(item)
            except Exception:
                log.exception("callback failed for item %r", item)
            finally:
                self.queue.task_done()
```
