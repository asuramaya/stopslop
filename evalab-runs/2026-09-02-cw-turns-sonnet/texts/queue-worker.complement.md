```python
import queue
import threading
import logging

logger = logging.getLogger(__name__)

_SHUTDOWN = object()


class QueueWorker:
    def __init__(self, callback, max_in_flight):
        self.callback = callback
        self.queue = queue.Queue(maxsize=max_in_flight)
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def submit(self, item, timeout=None):
        self.queue.put(item, timeout=timeout)

    def stop(self, timeout=None):
        self.queue.put(_SHUTDOWN)
        self._thread.join(timeout=timeout)

    def _run(self):
        while True:
            item = self.queue.get()
            if item is _SHUTDOWN:
                self.queue.task_done()
                break
            try:
                self.callback(item)
            except Exception:
                logger.exception("Error processing queue item: %r", item)
            finally:
                self.queue.task_done()
```
