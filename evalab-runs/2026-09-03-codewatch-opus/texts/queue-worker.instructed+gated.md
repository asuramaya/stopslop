```python
import logging
import queue
import threading

logger = logging.getLogger(__name__)


class _Shutdown:
    """Sentinel pushed onto the queue to tell the worker to stop consuming."""

    def __repr__(self):
        return "<shutdown>"


SHUTDOWN = _Shutdown()


class QueueWorker:
    """Consumes items from a queue on a background thread, one callback per item.

    A callback that raises is logged and the item is dropped; the thread keeps
    running. Pass ``on_error`` to route failures somewhere else (a dead-letter
    queue, a metrics counter). An ``on_error`` that itself raises is logged and
    swallowed so it can never take the thread down.

    ``max_in_flight`` caps how many items may be accepted but not yet handled.
    Once the cap is reached ``submit`` blocks (or raises, with ``block=False``)
    so a slow callback pushes back on producers instead of letting the queue
    grow without bound. The sentinel bypasses the cap so shutdown is always
    possible even when the worker is saturated.
    """

    def __init__(
        self,
        work_queue,
        handle_item,
        on_error=None,
        max_in_flight=100,
        name="queue-worker",
    ):
        self.work_queue = work_queue
        self.handle_item = handle_item
        self.on_error = on_error
        self.max_in_flight = max_in_flight
        self.thread = threading.Thread(target=self._run, name=name, daemon=True)
        self.processed = 0
        self.failed = 0
        self.rejected = 0
        self._stopping = threading.Event()
        self._slots = threading.BoundedSemaphore(max_in_flight)

    def start(self):
        self.thread.start()
        return self

    def _run(self):
        try:
            while True:
                item = self.work_queue.get()
                is_sentinel = item is SHUTDOWN
                try:
                    if is_sentinel:
                        return
                    self._handle_one(item)
                finally:
                    self.work_queue.task_done()
                    if not is_sentinel:
                        self._slots.release()
        except BaseException:
            logger.critical("worker loop died; queue is no longer being drained", exc_info=True)
            raise
        finally:
            self._stopping.set()
            logger.debug(
                "worker exiting after %d items (%d failed, %d rejected)",
                self.processed,
                self.failed,
                self.rejected,
            )

    def _handle_one(self, item):
        try:
            self.handle_item(item)
            self.processed += 1
        except Exception:
            self.failed += 1
            logger.exception("callback failed for item %r", item)
            if self.on_error is None:
                return
            try:
                self.on_error(item)
            except Exception:
                logger.exception("on_error handler failed for item %r", item)

    def submit(self, item, block=True, timeout=None):
        """Accept an item, waiting for an in-flight slot. False if it was refused."""
        if self._stopping.is_set():
            raise RuntimeError("worker is shutting down; item rejected")
        if not self._slots.acquire(blocking=block, timeout=timeout):
            self.rejected += 1
            logger.warning(
                "in-flight cap of %d reached; refused item %r", self.max_in_flight, item
            )
            return False
        try:
            self.work_queue.put(item)
        except BaseException:
            self._slots.release()
            raise
        return True

    def drain(self):
        """Block until every item queued so far has been handled."""
        self.work_queue.join()

    def stop(self, timeout=5.0):
        """Queue the sentinel and wait for the thread to finish its current item."""
        if not self.thread.is_alive():
            return
        self.work_queue.put(SHUTDOWN)
        self.thread.join(timeout)
        if self.thread.is_alive():
            logger.warning("worker thread did not exit within %.1fs", timeout)

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc, tb):
        self.stop()
        return False
```
