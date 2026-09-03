```python
"""Threaded queue worker: pulls items and hands each to a callback."""

import logging
import queue
import threading

log = logging.getLogger(__name__)

SHUTDOWN = object()


class QueueBackpressure(Exception):
    """Raised when submit() cannot enqueue within the caller's patience."""


class QueueWorker:
    """Consumes items from a queue.Queue on a background thread.

    max_in_flight bounds the queue, so a slow callback pushes back on the
    producer instead of letting the backlog grow without limit.
    """

    def __init__(
        self,
        callback,
        work_queue=None,
        on_error=None,
        max_in_flight=100,
        name="queue-worker",
    ):
        if work_queue is None:
            work_queue = queue.Queue(maxsize=max_in_flight)
        elif work_queue.maxsize <= 0:
            raise ValueError("a supplied work_queue must be bounded")
        self.callback = callback
        self.queue = work_queue
        self.on_error = on_error
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._started = False

    def start(self):
        if self._started:
            raise RuntimeError("worker already started")
        self._started = True
        self._thread.start()

    def submit(self, item, timeout=None):
        """Enqueue an item, blocking while the worker is at capacity.

        timeout=0 makes this a non-blocking try-submit.
        """
        if item is SHUTDOWN:
            raise ValueError("use stop() to shut the worker down")
        try:
            self.queue.put(item, block=timeout != 0, timeout=timeout or None)
        except queue.Full:
            raise QueueBackpressure(
                f"{self.queue.maxsize} items already in flight"
            ) from None

    def _run(self):
        while True:
            item = self.queue.get()
            try:
                if item is SHUTDOWN:
                    return
                self.callback(item)
            except Exception as exc:
                # One bad item must not kill the thread; the queue keeps draining.
                log.exception("callback failed for %r", item)
                self._report(item, exc)
            finally:
                # Runs on the sentinel path too, so a concurrent join() can finish.
                self.queue.task_done()

    def _report(self, item, exc):
        if self.on_error is None:
            return
        try:
            self.on_error(item, exc)
        except Exception:
            # The error handler is the last line of defence — if it throws too,
            # log and carry on rather than losing the worker to it.
            log.exception("on_error handler failed for %r", item)

    def join_pending(self):
        """Block until everything queued so far has been processed."""
        self.queue.join()

    def stop(self, timeout=5.0, drain=True):
        """Queue the sentinel and wait for the thread to wind down.

        With drain=True the sentinel goes behind the pending items, so they are
        all processed first; the thread exits on reaching it either way. The
        sentinel ignores the bound — a full queue must never block shutdown.
        """
        if not self._started:
            return
        if drain:
            self.queue.join()
        while True:
            try:
                self.queue.put(SHUTDOWN, timeout=0.1)
                break
            except queue.Full:
                if not self._thread.is_alive():
                    return
        self._thread.join(timeout)
        if self._thread.is_alive():
            log.warning("worker did not stop within %.1fs", timeout)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop(drain=exc_type is None)
        return False
```
