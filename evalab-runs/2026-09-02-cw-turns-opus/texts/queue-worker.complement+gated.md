```python
import logging
import queue
import threading

log = logging.getLogger(__name__)

_SHUTDOWN = object()


class QueueWorker:
    """Consume items from a queue on a background thread."""

    def __init__(self, callback, work_queue=None, name="queue-worker",
                 on_error=None, max_in_flight=100):
        if max_in_flight is not None and max_in_flight < 1:
            raise ValueError("max_in_flight must be at least 1")
        self._callback = callback
        self._on_error = on_error
        if work_queue is not None:
            self.queue = work_queue
        else:
            self.queue = queue.Queue(maxsize=max_in_flight or 0)
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._lock = threading.Lock()
        self._started = False
        self._stopped = False
        self.processed = 0
        self.failed = 0
        self.rejected = 0

    def start(self):
        with self._lock:
            if self._started:
                raise RuntimeError("worker already started")
            self._started = True
        self._thread.start()

    def submit(self, item, timeout=None):
        """Block until the worker has room, so a slow callback throttles producers."""
        if self._stopped:
            raise RuntimeError("worker is shutting down")
        try:
            self.queue.put(item, timeout=timeout)
        except queue.Full:
            self.rejected += 1
            raise

    def offer(self, item):
        """Non-blocking submit for producers that would rather drop than wait."""
        if self._stopped:
            raise RuntimeError("worker is shutting down")
        try:
            self.queue.put_nowait(item)
        except queue.Full:
            self.rejected += 1
            log.warning("queue full (%d in flight), dropped item %r",
                        self.queue.maxsize, item)
            return False
        return True

    def _run(self):
        while True:
            item = self.queue.get()
            if item is _SHUTDOWN:
                self.queue.task_done()
                return
            try:
                self._callback(item)
                self.processed += 1
            except Exception as exc:
                self.failed += 1
                self._handle_error(item, exc)
            finally:
                self.queue.task_done()

    def _handle_error(self, item, exc):
        """A failed item must not take the thread down with it."""
        if self._on_error is None:
            log.exception("callback failed for item %r", item)
            return
        try:
            self._on_error(item, exc)
        except Exception:
            log.exception("on_error hook failed for item %r", item)

    def join_pending(self):
        self.queue.join()

    def stop(self, timeout=None):
        """Drain the items queued so far, then retire the thread."""
        with self._lock:
            if not self._started or self._stopped:
                return
            self._stopped = True
        self.queue.put(_SHUTDOWN)
        self._thread.join(timeout)
        if self._thread.is_alive():
            log.warning("worker thread still alive after %s seconds", timeout)

    def in_flight(self):
        return self.queue.qsize()

    def is_alive(self):
        return self._thread.is_alive()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()
        return False
```
