```python
import logging
import queue
import threading

log = logging.getLogger(__name__)

_SHUTDOWN = object()


class QueueWorker:
    """Runs a callback against every item put on the queue, on one thread."""

    def __init__(
        self,
        callback,
        work_queue=None,
        name="queue-worker",
        on_error=None,
        max_in_flight=1000,
    ):
        if max_in_flight is not None and max_in_flight < 1:
            raise ValueError("max_in_flight must be at least 1")
        self._callback = callback
        self._on_error = on_error
        # The bound lives on the queue itself, so submit() blocks the producer
        # once the callback falls behind instead of growing the backlog forever.
        if work_queue is None:
            work_queue = queue.Queue(maxsize=max_in_flight or 0)
        self._queue = work_queue
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._started = False
        self._closed = False
        self.errors = 0
        self.dropped = 0

    @property
    def in_flight(self):
        return self._queue.qsize()

    def start(self):
        if self._started:
            raise RuntimeError("worker already started")
        self._started = True
        self._thread.start()

    def submit(self, item, timeout=None):
        """Block until there is room; raises queue.Full if timeout expires."""
        self._check_submittable(item)
        self._queue.put(item, block=True, timeout=timeout)

    def offer(self, item):
        """Non-blocking submit: returns False and counts a drop when full."""
        self._check_submittable(item)
        try:
            self._queue.put_nowait(item)
        except queue.Full:
            self.dropped += 1
            log.warning("queue full, dropped item %r", item)
            return False
        return True

    def _check_submittable(self, item):
        if self._closed:
            raise RuntimeError("worker is shutting down")
        if item is _SHUTDOWN:
            raise ValueError("cannot submit the shutdown sentinel")

    def _run(self):
        while True:
            item = self._queue.get()
            try:
                if item is _SHUTDOWN:
                    return
                self._callback(item)
            except Exception as exc:
                # One bad item must not kill the thread; the queue keeps draining.
                self.errors += 1
                log.exception("callback failed for item %r", item)
                self._report(item, exc)
            finally:
                self._queue.task_done()

    def _report(self, item, exc):
        if self._on_error is None:
            return
        try:
            self._on_error(item, exc)
        except Exception:
            # The error handler is the last line of defence, so it cannot be
            # allowed to propagate and take the thread down with it.
            log.exception("on_error handler failed for item %r", item)

    def join(self):
        self._queue.join()

    def stop(self, timeout=None):
        """Queue the sentinel so pending items run first, then wait for the thread."""
        if not self._started or self._closed:
            return
        self._closed = True
        # A bounded queue can be full here, so this put waits for the worker to
        # free a slot rather than deadlocking a caller that expected no block.
        self._queue.put(_SHUTDOWN)
        self._thread.join(timeout)
        if self._thread.is_alive():
            raise TimeoutError(f"worker did not stop within {timeout} seconds")
        self._started = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()
        return False
```
