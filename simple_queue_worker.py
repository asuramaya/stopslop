"""Background queue consumer, minimal version."""

import logging
import queue
import threading
import time


class _Stop:
    """Default end-of-stream marker. Compares by identity."""

    def __repr__(self):
        return "STOP"


STOP = _Stop()

logger = logging.getLogger(__name__)


class WorkerDead(RuntimeError):
    """Raised by put() when the consumer thread is gone."""


class QueueWorker:
    """Runs a callback over items pulled from a queue in one background thread.

    A callback exception is passed to on_error, or logged if there is no
    on_error, and the item dropped; the worker keeps going. Anything that
    is not an Exception -- KeyboardInterrupt, SystemExit, MemoryError --
    is logged and does end the thread, but it is recorded first, so a
    later put() raises WorkerDead instead of filling a queue nobody reads.

    Shutdown travels in band: the thread exits on the first item equal to
    the sentinel, so anything already queued is processed first. stop()
    puts the sentinel for you; a producer can also put it directly to end
    the stream at a point of its own choosing. Pass sentinel= to pick a
    different value (None is a common one) when STOP cannot travel over
    whatever fills the queue.

    max_in_flight bounds the items accepted but not yet finished, counting
    the one inside the callback. At the limit put() blocks, or raises
    queue.Full when given block=False or a timeout that runs out. This is
    the bound that maxsize= does not give you: an item in the callback has
    left the queue, so maxsize=n still lets n+1 items be outstanding, and
    a callback that never returns holds its slot for as long as it runs.
    """

    def __init__(self, callback, maxsize=0, name="queue-worker", sentinel=STOP,
                 on_error=None, max_in_flight=None):
        if max_in_flight is not None and max_in_flight < 1:
            raise ValueError("max_in_flight must be >= 1")
        self.callback = callback
        self.sentinel = sentinel
        self.on_error = on_error
        self.max_in_flight = max_in_flight
        self._slots = None if max_in_flight is None else threading.Semaphore(max_in_flight)
        self.queue = queue.Queue(maxsize=maxsize)
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._started = False
        self._crash = None

    def start(self):
        if self._started:
            raise RuntimeError("worker already started")
        self._started = True
        self._thread.start()
        return self

    @property
    def crash(self):
        """The BaseException that killed the thread, or None."""
        return self._crash

    def put(self, item, block=True, timeout=None):
        self._check_alive()
        if self._slots is None:
            self.queue.put(item, block=block, timeout=timeout)
            return
        deadline = None if timeout is None else time.monotonic() + timeout
        # Semaphore.acquire rejects a timeout when blocking=False; drop it.
        got = self._slots.acquire(True, timeout) if block else self._slots.acquire(False)
        if not got:
            raise queue.Full("max_in_flight reached")
        try:
            # Waiting for a slot can outlast the thread; re-check before committing.
            self._check_alive()
            self.queue.put(item, block=block, timeout=self._remaining(deadline))
        except BaseException:
            self._slots.release()
            raise

    @staticmethod
    def _remaining(deadline):
        if deadline is None:
            return None
        return max(0.0, deadline - time.monotonic())

    def _check_alive(self):
        if self._crash is not None:
            raise WorkerDead("consumer thread died") from self._crash

    def join(self):
        """Block until every item put so far has been processed."""
        self.queue.join()

    def stop(self, timeout=None):
        """Ask the thread to finish the backlog and exit, then wait for it."""
        if not self._started:
            return
        if self._thread.is_alive():
            # Bypasses the in-flight limit deliberately: stop() must not queue
            # behind the backlog it is trying to end.
            self.queue.put(self.sentinel)
        self._thread.join(timeout)

    def _is_sentinel(self, item):
        return item is self.sentinel or item == self.sentinel

    def _handle_error(self, exc, item):
        if self.on_error is None:
            logger.exception("queue worker callback failed on %r", item)
            return
        try:
            self.on_error(exc, item)
        except Exception:
            logger.exception("queue worker on_error failed on %r", item)

    def _release_all(self):
        """Hand out every slot at once so blocked producers wake and see the crash."""
        if self._slots is not None:
            for _ in range(self.max_in_flight):
                self._slots.release()

    def _run(self):
        item = None
        try:
            while True:
                item = self.queue.get()
                stopping = False
                try:
                    stopping = self._is_sentinel(item)
                    if stopping:
                        return
                    self.callback(item)
                except Exception as exc:
                    self._handle_error(exc, item)
                finally:
                    self.queue.task_done()
                    # The item that ends the loop keeps its slot: nothing after
                    # it is consumed, so there is no producer left to admit.
                    if self._slots is not None and not stopping:
                        self._slots.release()
        except BaseException as exc:
            self._crash = exc
            logger.exception("queue worker thread died on %r", item)
            self._release_all()
            raise

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc_info):
        self.stop()
        return False
