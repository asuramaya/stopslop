```python
import threading
import queue
import logging
from typing import Callable


logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class _STOP_SENTINEL:
    """Sentinel value to signal worker shutdown."""
    pass


class QueueWorker:
    def __init__(self, callback: Callable, num_workers: int = 1, max_in_flight: int = 10):
        self.callback = callback
        self.queue = queue.Queue()
        self.num_workers = num_workers
        self.max_in_flight = max_in_flight
        self.semaphore = threading.Semaphore(max_in_flight)
        self.threads = []
        self.running = False

    def start(self):
        """Start worker threads."""
        self.running = True
        for _ in range(self.num_workers):
            t = threading.Thread(target=self._worker_loop, daemon=False)
            t.start()
            self.threads.append(t)

    def _worker_loop(self):
        """Process items from queue until sentinel received."""
        while True:
            try:
                item = self.queue.get(timeout=1)
                
                if isinstance(item, _STOP_SENTINEL):
                    self.queue.task_done()
                    break
                
                self.semaphore.acquire()
                try:
                    self.callback(item)
                except Exception as e:
                    logger.exception(f"Error processing item {item}: {e}")
                finally:
                    self.semaphore.release()
                    self.queue.task_done()
            except queue.Empty:
                continue

    def put(self, item):
        """Add item to queue."""
        self.queue.put(item)

    def stop(self):
        """Stop all workers gracefully by sending sentinel values."""
        self.running = False
        for _ in range(self.num_workers):
            self.queue.put(_STOP_SENTINEL())
        for t in self.threads:
            t.join()

    def wait(self):
        """Block until all items processed."""
        self.queue.join()


if __name__ == "__main__":
    import time
    
    def process(item):
        if item == 2:
            raise ValueError("Test error")
        time.sleep(0.5)
        print(f"Processing: {item}")

    worker = QueueWorker(callback=process, num_workers=2, max_in_flight=3)
    worker.start()
    for i in range(5):
        worker.put(i)
    worker.wait()
    worker.stop()
```
