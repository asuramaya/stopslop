"""Background thread that runs a callback over items from a queue."""

import logging
import queue
import threading


_STOP = object()

logger = logging.getLogger(__name__)


class ThreadWorker:
    """Pulls items off a queue in one background thread and calls ``callback``.

    A callback exception is logged and the item dropped; the loop keeps going.
    ``maxsize`` bounds the backlog, so ``put()`` blocks once the producer gets
    that far ahead of the callback.
    """

    def __init__(self, callback, maxsize=0, name="thread-worker"):
        self.callback = callback
        self.queue = queue.Queue(maxsize=maxsize)
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)

    def start(self):
        self._thread.start()
        return self

    def put(self, item, block=True, timeout=None):
        self.queue.put(item, block=block, timeout=timeout)

    def join(self):
        """Block until every item put so far has been processed."""
        self.queue.join()

    def stop(self, timeout=None):
        """Queue a shutdown marker behind the backlog and wait for the thread."""
        if self._thread.is_alive():
            self.queue.put(_STOP)
        self._thread.join(timeout)

    def _run(self):
        while True:
            item = self.queue.get()
            try:
                if item is _STOP:
                    return
                self.callback(item)
            except Exception:
                logger.exception("callback failed on %r", item)
            finally:
                self.queue.task_done()

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc_info):
        self.stop()
        return False
