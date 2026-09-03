```python
"""A queue-backed worker thread that hands each item to a callback."""

import logging
import queue
import threading

log = logging.getLogger(__name__)

#: Put this on the queue to ask the worker to finish and exit.
SHUTDOWN = object()


class QueueWorker:
    """Consumes items from a queue.Queue on a background thread.

    `max_in_flight` caps how many items may sit unprocessed. Once the queue is
    full, `put()` blocks (or raises with `block=False` / a `timeout`), pushing
    backpressure onto the producer instead of letting an unbounded backlog grow
    behind a slow callback. Exceptions from the callback go to `on_error` and
    the loop continues; SHUTDOWN ends it after the pending items drain.
    """

    def __init__(self, callback, max_in_flight=100, q=None, on_error=None,
                 name="queue-worker", daemon=True):
        self.callback = callback
        self.on_error = on_error or self._log_error
        self.queue = q if q is not None else queue.Queue(maxsize=max_in_flight)
        self.error_count = 0
        self.dropped_count = 0
        self._thread = threading.Thread(target=self._run, name=name, daemon=daemon)
        self._started = False
        self._stopping = False

    @staticmethod
    def _log_error(item, exc):
        log.exception("callback failed for item %r", item, exc_info=exc)

    def start(self):
        if self._started:
            raise RuntimeError("worker already started")
        self._started = True
        self._thread.start()
        return self

    def put(self, item, block=True, timeout=None):
        """Enqueue an item, blocking while the worker is at capacity."""
        if self._stopping:
            raise RuntimeError("worker is shutting down")
        self.queue.put(item, block=block, timeout=timeout)

    def offer(self, item, timeout=None):
        """Non-fatal put: drop the item and return False if still full."""
        try:
            self.put(item, block=timeout is not None, timeout=timeout)
            return True
        except queue.Full:
            self.dropped_count += 1
            log.warning("queue full (%d in flight); dropping %r", self.qsize(), item)
            return False

    def qsize(self):
        return self.queue.qsize()

    def _run(self):
        while True:
            item = self.queue.get()
            try:
                if item is SHUTDOWN:
                    log.debug("shutdown sentinel received; worker exiting")
                    return
                self.callback(item)
            except Exception as exc:
                self.error_count += 1
                try:
                    self.on_error(item, exc)
                except Exception:  # a broken error handler must not kill us
                    log.exception("on_error hook raised for item %r", item)
            finally:
                self.queue.task_done()

    def join_queue(self):
        """Block until every item queued so far has been processed."""
        self.queue.join()

    def stop(self, timeout=None):
        """Queue the sentinel and wait for the thread to drain and exit.

        Idempotent. Returns True if the thread actually finished.
        """
        if not self._started:
            return True
        if not self._stopping:
            self.queue.put(SHUTDOWN)  # blocks if full; the worker keeps draining
            self._stopping = True
        self._thread.join(timeout)
        return not self._thread.is_alive()

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    def work(n):
        if n == 3:
            raise ValueError("three is bad")
        print(f"got {n} -> {n * n}")

    with QueueWorker(work, max_in_flight=4) as worker:
        for i in range(10):
            worker.put(i)          # blocks once 4 are in flight
        worker.offer(99, timeout=0.5)
        worker.join_queue()
        print("errors:", worker.error_count, "dropped:", worker.dropped_count)
```

The cap is `queue.Queue(maxsize=max_in_flight)`, so backpressure comes from the queue itself rather than a separate semaphore — one less thing to keep in sync with `get()`/`task_done()`. `put()` blocks by default, which is what you want when the producer can afford to wait; `offer()` is the shed-load variant that drops and counts instead, so a producer that must not block (a socket reader, a signal handler) has a path that doesn't stall the whole pipeline.

Two things this changes. `put()` can now block indefinitely — pass a `timeout` and handle `queue.Full` if your producer has a deadline. And `stop()` blocks too when the queue is full, since the sentinel has to fit; that's deliberate (it preserves "everything already queued runs first"), but it means `stop(timeout=5)` bounds only the thread join, not the enqueue. If you need a hard bound on shutdown, add a `threading.Event` the loop checks and abandon the backlog.

If you pass your own `q`, note that `max_in_flight` is ignored — the bound is whatever that queue was built with.
