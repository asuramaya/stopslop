```python
import threading
import queue
from typing import Callable, Any
import traceback


class QueueWorker:
    """Worker that processes queue items with limited concurrency."""
    
    _SENTINEL = object()
    
    def __init__(self, callback: Callable[[Any], None], q: queue.Queue = None,
                 error_handler: Callable[[Exception], None] = None,
                 max_inflight: int = 4):
        self.callback = callback
        self.queue = q or queue.Queue()
        self.main_thread = None
        self.error_handler = error_handler or self._print_error
        self.semaphore = threading.Semaphore(max_inflight)
        self.workers = []
    
    def start(self):
        """Start the worker thread."""
        if self.main_thread and self.main_thread.is_alive():
            return
        self.main_thread = threading.Thread(target=self._run, daemon=False)
        self.main_thread.start()
    
    def stop(self):
        """Stop and wait for all processing to complete."""
        self.queue.put(self._SENTINEL)
        self.main_thread.join()
        for t in self.workers:
            t.join()
    
    def _run(self):
        """Main loop dispatching items to worker threads."""
        while True:
            item = self.queue.get()
            if item is self._SENTINEL:
                self.queue.task_done()
                break
            self.semaphore.acquire()
            t = threading.Thread(target=self._process, args=(item,),
                                daemon=True)
            self.workers.append(t)
            t.start()
            self.queue.task_done()
    
    def _process(self, item):
        """Process item and release semaphore slot."""
        try:
            self.callback(item)
        except Exception as e:
            self.error_handler(e)
        finally:
            self.semaphore.release()
    
    @staticmethod
    def _print_error(error):
        """Default error handler."""
        print(f"Error processing item: {error}")
        traceback.print_exc()


if __name__ == "__main__":
    def process_item(item):
        print(f"Processing: {item}")
    
    worker = QueueWorker(process_item, max_inflight=2)
    worker.start()
    for i in range(5):
        worker.queue.put(i)
    worker.stop()
```
