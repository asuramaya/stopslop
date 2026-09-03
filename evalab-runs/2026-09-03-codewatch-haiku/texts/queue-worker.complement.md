```python
import threading
import queue
import logging
from typing import Callable, Any


logger = logging.getLogger(__name__)
SENTINEL = object()


class QueueWorker:
    """Worker thread that processes items from a queue."""
    
    def __init__(self, callback: Callable[[Any], None], max_queue_size: int = 10):
        self.callback = callback
        self.queue = queue.Queue(maxsize=max_queue_size)
        self.thread = threading.Thread(target=self._run, daemon=False)
        self.thread.start()
    
    def _run(self) -> None:
        while True:
            try:
                item = self.queue.get(timeout=0.1)
            except queue.Empty:
                continue
            
            if item is SENTINEL:
                break
            
            try:
                self.callback(item)
            except Exception:
                logger.exception(f"Error processing {item}")
            finally:
                self.queue.task_done()
    
    def put(self, item: Any) -> None:
        self.queue.put(item)
    
    def stop(self, timeout: float = None) -> None:
        self.queue.put(SENTINEL)
        self.thread.join(timeout=timeout)
    
    def wait(self) -> None:
        self.queue.join()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    def callback(item):
        if item == 3:
            raise ValueError("test error")
        print(f"Processing: {item}")
    
    worker = QueueWorker(callback, max_queue_size=2)
    for i in range(5):
        worker.put(i)
    worker.wait()
    worker.stop()
```
