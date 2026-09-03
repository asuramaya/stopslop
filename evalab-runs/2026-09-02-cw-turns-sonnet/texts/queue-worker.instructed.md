```python
import logging
import queue
import threading

logger = logging.getLogger(__name__)

_SHUTDOWN = object()


class QueueWorker:
    def __init__(self, callback, maxsize=0, max_inflight=1):
        self.queue = queue.Queue(maxsize=maxsize)
        self.callback = callback
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._inflight = threading.Semaphore(max_inflight)

    def start(self):
        self._thread.start()

    def _run(self):
        while True:
            item = self.queue.get()
            if item is _SHUTDOWN:
                self.queue.task_done()
                break
            self._inflight.acquire()
            try:
                self.callback(item)
            except Exception:
                logger.exception("callback failed for item: %r", item)
            finally:
                self._inflight.release()
                self.queue.task_done()

    def submit(self, item):
        self.queue.put(item)

    def stop(self, wait=True):
        self.queue.put(_SHUTDOWN)
        if wait:
            self._thread.join()

    def join(self):
        self.queue.join()
```
