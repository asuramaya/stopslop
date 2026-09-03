```python
import logging
import queue
import threading

log = logging.getLogger(__name__)


class _Shutdown:
    """Sentinel type so a bare object() can never be confused with a real item."""

    def __repr__(self):
        return "<shutdown>"


SHUTDOWN = _Shutdown()


class QueueWorker:
    """Drains a queue.Queue on a background thread, handing each item to a callback.

    max_in_flight bounds the number of items accepted but not yet finished. Once
    that many are outstanding, submit() blocks (or raises, with block=False)
    rather than letting an unbounded backlog accumulate behind a slow callback.
    """

    def __init__(
        self,
        callback,
        q=None,
        name="queue-worker",
        on_error=None,
        max_in_flight=100,
    ):
        if max_in_flight is not None and max_in_flight < 1:
            raise ValueError("max_in_flight must be at least 1")
        self.callback = callback
        # The sentinel needs a free slot at shutdown even when the queue is
        # saturated, so the queue itself holds one more than the caller's limit.
        maxsize = 0 if max_in_flight is None else max_in_flight + 1
        self.queue = q if q is not None else queue.Queue(maxsize=maxsize)
        self.on_error = on_error
        self.max_in_flight = max_in_flight
        self._slots = None if max_in_flight is None else threading.Semaphore(max_in_flight)
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._started = False
        self._stopped = threading.Event()
        self.error_count = 0

    def start(self):
        if self._started:
            raise RuntimeError("worker already started")
        self._started = True
        self._thread.start()
        return self

    def submit(self, item, block=True, timeout=None):
        """Enqueue an item, waiting for an in-flight slot. Returns False if full."""
        if self._stopped.is_set():
            raise RuntimeError("worker is shutting down")
        if self._slots is not None and not self._slots.acquire(block, timeout):
            return False
        try:
            self.queue.put(item)
        except BaseException:
            if self._slots is not None:
                self._slots.release()
            raise
        return True

    def _handle_error(self, item):
        self.error_count += 1
        log.exception("callback failed for item %r", item)
        if self.on_error is None:
            return
        try:
            self.on_error(item)
        except Exception:
            # A broken error handler must not take the thread down with it.
            log.exception("on_error hook failed for item %r", item)

    def _run(self):
        while True:
            item = self.queue.get()
            is_sentinel = item is SHUTDOWN
            try:
                if is_sentinel:
                    return
                self.callback(item)
            except Exception:
                self._handle_error(item)
            except BaseException:
                # KeyboardInterrupt/SystemExit are not ours to swallow, but the
                # slot and the task_done below still have to be settled.
                log.exception("worker thread aborting on item %r", item)
                raise
            finally:
                if self._slots is not None and not is_sentinel:
                    self._slots.release()
                self.queue.task_done()

    def join_queue(self):
        self.queue.join()

    def stop(self, timeout=None, drain=True):
        """Queue the sentinel and wait for the thread to reach it.

        Items already queued are processed first, since the sentinel sits behind
        them in FIFO order. drain=False skips waiting on the queue itself and
        only bounds the thread join.
        """
        if not self._started or self._stopped.is_set():
            return
        self._stopped.set()
        self.queue.put(SHUTDOWN)
        if drain:
            self.queue.join()
        self._thread.join(timeout)
        if self._thread.is_alive():
            log.warning("worker thread did not exit within %s seconds", timeout)

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc, tb):
        self.stop()
        return False
```
