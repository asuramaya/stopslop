```python
import queue
import threading
import logging
from typing import Callable, Any, Optional


logger = logging.getLogger(__name__)

_SHUTDOWN_SENTINEL = object()


class QueueWorker:
    def __init__(
        self,
        process_fn: Callable,
        queue_size: int = 0,
        error_fn: Optional[Callable[[Any, Exception], None]] = None,
        max_inflight: int = 1,
    ):
        self.process_fn = process_fn
        self.error_fn = error_fn
        self.task_queue = queue.Queue(maxsize=queue_size)
        self.inflight_semaphore = threading.Semaphore(max_inflight)
        self.thread = None
        self.running = False
    
    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._process_loop, daemon=False)
        self.thread.start()
    
    def stop(self, timeout: Optional[float] = None) -> None:
        if not self.running:
            return
        self.running = False
        self.task_queue.put(_SHUTDOWN_SENTINEL)
        if self.thread:
            self.thread.join(timeout=timeout)
    
    def submit(self, item: Any) -> None:
        if not self.running:
            raise RuntimeError("Worker not started")
        self.task_queue.put(item)
    
    def _process_loop(self) -> None:
        while True:
            try:
                item = self.task_queue.get(timeout=1.0)
            except queue.Empty:
                continue
            
            if item is _SHUTDOWN_SENTINEL:
                break
            
            self.inflight_semaphore.acquire()
            try:
                self.process_fn(item)
            except Exception as e:
                if self.error_fn:
                    self.error_fn(item, e)
                else:
                    logger.exception("Error processing item")
            finally:
                self.inflight_semaphore.release()


if __name__ == "__main__":
    def process_item(item):
        logger.info(f"Processing: {item}")
        if item == 2:
            raise ValueError("Test error")
    
    def handle_error(item, error):
        logger.error(f"Failed to process {item}: {error}")
    
    worker = QueueWorker(process_item, error_fn=handle_error, max_inflight=3)
    worker.start()
    
    for i in range(5):
        worker.submit(i)
    
    worker.stop(timeout=5)
```
