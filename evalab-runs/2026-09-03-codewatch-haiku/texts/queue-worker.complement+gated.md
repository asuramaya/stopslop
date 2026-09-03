```python
import logging
import queue
import threading
from typing import Callable, Any

logger = logging.getLogger(__name__)


class QueueWorker:
    _SENTINEL = object()
    
    def __init__(self, callback: Callable[[Any], None], max_in_flight: int = 10):
        self.queue = queue.Queue()
        self.callback = callback
        self.semaphore = threading.Semaphore(max_in_flight)
        self.thread = None

    def _worker(self):
        while True:
            try:
                item = self.queue.get(timeout=0.5)
            except queue.Empty:
                continue
            
            if item is self._SENTINEL:
                break
            
            with self.semaphore:
                try:
                    self.callback(item)
                except Exception:
                    logger.exception("Callback failed for item")
                finally:
                    self.queue.task_done()

    def start(self):
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def stop(self):
        self.queue.put(self._SENTINEL)
        if self.thread:
            self.thread.join(timeout=5)

    def put(self, item: Any):
        self.queue.put(item)

    def join(self):
        self.queue.join()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    def process_item(item):
        print(f"Processing: {item}")

    worker = QueueWorker(process_item, max_in_flight=3)
    worker.start()
    
    for i in range(5):
        worker.put(i)
    
    worker.join()
    worker.stop()
```
