```python
import queue
import threading
import logging

logger = logging.getLogger(__name__)

_SENTINEL = object()


class QueueWorker:
    def __init__(self, callback, maxsize=0, max_inflight=1):
        self.queue = queue.Queue(maxsize=maxsize)
        self.callback = callback
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._stopped = threading.Event()
        self._inflight = threading.Semaphore(max_inflight)

    def start(self):
        self._thread.start()

    def submit(self, item):
        if self._stopped.is_set():
            raise RuntimeError("cannot submit to a stopped worker")
        self.queue.put(item)

    def stop(self, timeout=None):
        self._stopped.set()
        self.queue.put(_SENTINEL)
        self._thread.join(timeout=timeout)

    def _run(self):
        while True:
            item = self.queue.get()
            if item is _SENTINEL:
                self.queue.task_done()
                break
            self._inflight.acquire()
            try:
                self.callback(item)
            except Exception:
                logger.exception("callback failed for item %r", item)
            finally:
                self._inflight.release()
                self.queue.task_done()
```
