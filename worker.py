"""Background thread that runs a callback over items from a queue."""

import logging
import queue
import threading
import time

logger = logging.getLogger(__name__)


class _Stop:
    """Type of the STOP sentinel. Private so STOP stays a singleton."""

    def __repr__(self):
        return "STOP"


STOP = _Stop()
"""Put this on the queue to shut the worker down after the backlog drains."""


class Worker:
    """Pulls items off a queue and hands each one to `callback`.

    The callback runs on the worker thread. Exceptions from it are logged
    and the worker keeps going, so one bad item cannot kill the loop.

    Shutdown is by sentinel: the thread exits when it pulls `STOP` off the
    queue, which means every item queued ahead of it is processed first.
    Producers sharing the queue can put STOP directly; `stop()` is the
    convenience path that also joins the thread.

    `max_pending` bounds how many items can sit in the queue at once. Once
    the bound is reached `put()` blocks the producer until the callback
    frees a slot, so a slow callback pushes back on whoever feeds it instead
    of letting the backlog grow without limit.
    """

    def __init__(self, callback, q=None, name="worker", max_pending=0):
        if q is not None and max_pending:
            raise ValueError("pass max_pending or q, not both: set maxsize on your own queue")
        self.callback = callback
        self.queue = q if q is not None else queue.Queue(maxsize=max_pending)
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._lock = threading.Lock()
        self._started = False
        self._stopping = False

    def start(self):
        if self._started:
            raise RuntimeError("worker already started")
        self._started = True
        self._thread.start()
        return self

    def put(self, item, block=True, timeout=None):
        """Hand an item to the worker, blocking while the queue is full.

        Raises `queue.Full` if `block` is false, or if `timeout` expires.
        """
        self.queue.put(item, block, timeout)

    def try_put(self, item):
        """Non-blocking `put`. Returns False instead of raising when full."""
        try:
            self.queue.put_nowait(item)
        except queue.Full:
            return False
        return True

    @property
    def pending(self):
        """Approximate count of items waiting, plus any item in the callback."""
        return self.queue.qsize()

    @property
    def running(self):
        return self._started and self._thread.is_alive()

    def _run(self):
        while True:
            item = self.queue.get()
            try:
                if item is STOP:
                    return
                self.callback(item)
            except Exception:
                logger.exception("callback failed for %r", item)
            finally:
                self.queue.task_done()

    def join(self):
        """Block until every item queued so far has been processed."""
        self.queue.join()

    def stop(self, timeout=None):
        """Ask the thread to finish the backlog, then exit.

        Idempotent, and safe if a producer already sent STOP itself: at most
        one sentinel is ever enqueued from here, so `join()` cannot be left
        waiting on an unconsumed one.
        """
        with self._lock:
            if not self._started or self._stopping:
                send = False
            else:
                self._stopping = True
                send = self._thread.is_alive()
        if send:
            self._send_stop(timeout)
        if self._started:
            self._thread.join(timeout)

    def _send_stop(self, timeout):
        """Enqueue STOP without deadlocking on a full bounded queue.

        A plain `put` would block forever if the queue is full and the thread
        has already exited, so retry in short slices and give up once the
        thread is gone or `timeout` runs out.
        """
        deadline = None if timeout is None else time.monotonic() + timeout
        while self._thread.is_alive():
            if deadline is not None and time.monotonic() >= deadline:
                return
            try:
                self.queue.put(STOP, timeout=0.05)
            except queue.Full:
                continue
            return

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()
