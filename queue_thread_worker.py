import logging
import queue
import threading

logger = logging.getLogger(__name__)


class QueueWorker:
    """Runs a callback on items pulled from a queue.Queue in a background thread."""

    _STOP = object()

    def __init__(self, callback, maxsize=100):
        self._callback = callback
        self._queue = queue.Queue(maxsize=maxsize)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._started = False

    def start(self):
        if not self._started:
            self._started = True
            self._thread.start()

    def submit(self, item):
        self._queue.put(item)

    def stop(self, wait=True):
        self._queue.put(self._STOP)
        if wait:
            self._thread.join()

    def _run(self):
        while True:
            item = self._queue.get()
            try:
                if item is self._STOP:
                    return
                self._callback(item)
            except Exception:
                logger.exception("callback failed for item: %r", item)
            finally:
                self._queue.task_done()


if __name__ == "__main__":
    def handle(item):
        print(f"processed: {item}")

    worker = QueueWorker(handle)
    worker.start()
    for i in range(5):
        worker.submit(i)
    worker.stop()
