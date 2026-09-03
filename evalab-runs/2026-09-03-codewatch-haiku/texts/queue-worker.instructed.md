```python
import queue
import threading
import logging
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)


class QueueWorker:
    SHUTDOWN_SENTINEL = object()
    
    def __init__(self, callback: Callable[[Any], None], queue_obj: Optional[queue.Queue] = None, max_in_flight: int = 10):
        self.callback = callback
        self.queue = queue_obj or queue.Queue()
        self.max_in_flight = max_in_flight
        self.in_flight_semaphore = threading.Semaphore(max_in_flight)
        self.thread = None
        self.running = False

    def start(self) -> None:
        if self.running:
            raise RuntimeError("Worker already running")
        self.running = True
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.running = False
        self.queue.put(self.SHUTDOWN_SENTINEL)
        if self.thread:
            self.thread.join(timeout=5)

    def put(self, item: Any) -> None:
        self.in_flight_semaphore.acquire()
        self.queue.put(item)

    def _process_queue(self) -> None:
        while self.running:
            try:
                item = self.queue.get(timeout=1)
            except queue.Empty:
                continue
            
            if item is self.SHUTDOWN_SENTINEL:
                break
            
            try:
                self.callback(item)
            except Exception as e:
                logger.exception(f"Callback failed for item: {item}")
            finally:
                self.in_flight_semaphore.release()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    def process_item(item):
        pass

    worker = QueueWorker(process_item, max_in_flight=5)
    worker.start()
    worker.put("task1")
    worker.put("task2")
    worker.put("task3")

    import time
    time.sleep(1)
    worker.stop()
```
