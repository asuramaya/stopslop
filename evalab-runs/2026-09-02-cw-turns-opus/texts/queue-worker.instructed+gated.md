```python
import logging
import queue
import threading

logger = logging.getLogger(__name__)

_SHUTDOWN = object()


class QueueWorker:
    """Runs a callback against each item pushed onto an internal queue.

    Items are handled by a pool of threads, so one slow callback occupies a
    single thread instead of stalling everything behind it. `max_in_flight`
    caps how many callbacks run at once; `max_pending` caps how many items
    can wait, so submit() applies backpressure once the pool is saturated.
    """

    def __init__(self, handler, name="queue-worker", max_pending=0,
                 max_in_flight=1, on_error=None):
        if max_in_flight < 1:
            raise ValueError("max_in_flight must be at least 1")
        self.handler = handler
        self.on_error = on_error
        self.queue = queue.Queue(maxsize=max_pending)
        self.max_in_flight = max_in_flight
        self.threads = [
            threading.Thread(target=self._drain, name=f"{name}-{n}", daemon=True)
            for n in range(max_in_flight)
        ]
        self.handled = 0
        self.failed = 0
        self.in_flight = 0
        self._lock = threading.Lock()
        self._state = "new"

    def start(self):
        with self._lock:
            if self._state != "new":
                raise RuntimeError(f"worker is {self._state}, cannot start")
            self._state = "running"
        for thread in self.threads:
            thread.start()

    def submit(self, item, block=True, timeout=None):
        with self._lock:
            if self._state != "running":
                raise RuntimeError(f"worker is {self._state}, not accepting items")
        self.queue.put(item, block=block, timeout=timeout)

    def _drain(self):
        while True:
            item = self.queue.get()
            try:
                if item is _SHUTDOWN:
                    logger.debug("sentinel received, draining stopped")
                    return
                with self._lock:
                    self.in_flight += 1
                try:
                    self.handler(item)
                finally:
                    with self._lock:
                        self.in_flight -= 1
                with self._lock:
                    self.handled += 1
            except Exception as exc:
                with self._lock:
                    self.failed += 1
                logger.exception("handler failed for %r", item)
                self._report(item, exc)
            except BaseException:
                # KeyboardInterrupt/SystemExit reaching a worker thread means the
                # process is going down; log it so the exit is not silent, then let go.
                logger.exception("worker thread aborting on %r", item)
                raise
            finally:
                self.queue.task_done()

    def _report(self, item, exc):
        if self.on_error is None:
            return
        try:
            self.on_error(item, exc)
        except Exception:
            logger.exception("on_error callback failed for %r", item)

    def join(self):
        """Blocks until everything submitted so far has been handled."""
        self.queue.join()

    def stop(self, timeout=None):
        """Queues one sentinel per thread behind pending items and waits."""
        with self._lock:
            if self._state != "running":
                return
            self._state = "stopping"
        for _ in self.threads:
            self.queue.put(_SHUTDOWN)
        for thread in self.threads:
            thread.join(timeout)
        alive = [thread.name for thread in self.threads if thread.is_alive()]
        if alive:
            logger.warning("threads still alive after %ss: %s", timeout, ", ".join(alive))
        else:
            self._state = "stopped"
            logger.debug("worker stopped: %d handled, %d failed", self.handled, self.failed)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()
        return False
```
