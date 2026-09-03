`queue_worker.py:1` — 62 lines, smoke-tested above (three items processed in order, the `1/0` item routed to `on_error` without killing the thread).

Design points:

- **Sentinel is a private module object**, not `None` or a string, so any user value is a legal queue item.
- **`task_done()` in `finally`** — pairs with `queue.join()` in `stop(drain=True)`, and stays balanced even when the callback raises.
- **The sentinel is enqueued after the drain**, so `stop()` waits for the backlog and then exits. `stop(drain=False)` skips the join and drops whatever is still queued.
- **Callback exceptions go to `on_error(item, exc)`** and are otherwise swallowed; a bare `raise` inside your `on_error` still propagates and ends the thread, if you want that.
- Thread is a daemon, so a forgotten `stop()` doesn't hang interpreter exit — but the context manager is the intended path.

One thing worth naming: this is a single consumer thread. If you want N workers, the drain logic needs N sentinels (or a shared `threading.Event` checked alongside the get), because one sentinel only stops one thread.
