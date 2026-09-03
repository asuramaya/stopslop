```python
import logging
import queue
import threading

logger = logging.getLogger(__name__)

_SHUTDOWN = object()


class QueueWorker:
    """Runs a callback on each item pulled from a queue.Queue, on a background thread."""

    def __init__(self, work_queue: queue.Queue, callback, name: str = "queue-worker", max_in_flight: int = 1):
        self._queue = work_queue
        self._callback = callback
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._in_flight = threading.Semaphore(max_in_flight)

    def start(self):
        self._thread.start()

    def stop(self, timeout: float = None):
        self._queue.put(_SHUTDOWN)
        self._thread.join(timeout=timeout)

    def _run(self):
        while True:
            item = self._queue.get()
            if item is _SHUTDOWN:
                self._queue.task_done()
                break
            self._in_flight.acquire()
            try:
                self._callback(item)
            except Exception:
                logger.exception("callback raised while processing item: %r", item)
            finally:
                self._in_flight.release()
                self._queue.task_done()


def start_worker(work_queue: queue.Queue, callback, name: str = "queue-worker", max_in_flight: int = 1) -> QueueWorker:
    worker = QueueWorker(work_queue, callback, name=name, max_in_flight=max_in_flight)
    worker.start()
    return worker
```
