`token_bucket.py` doesn't use `time.time()` — it's been `time.monotonic` since I wrote it (`token_bucket.py:29`, the `clock=time.monotonic` default). Nothing in this tree uses `time.time()`: `rate_limiter.py:14`, `lru_cache.py`, `queue_worker.py` and the rest all take monotonic too. So there's no wall-clock jump to fix, and I've made no change.

On drift under load specifically, the refill math doesn't accumulate error by construction. `_refill` (`:46`) recomputes `elapsed = now - self._updated` against a stored timestamp and then sets `_updated = now`. It never adds a fixed tick or rounds to an interval, so a slow or contended call just means one larger `elapsed` — the tokens granted over any span depend only on the endpoints, not on how many times `_refill` ran in between.

Measured it to be sure, `rate=500, capacity=1`, spinning on `try_acquire`:

- Single thread, 2.000s: 997 grants against ~1001 expected.
- 8 threads contending, 2.052s: 1026 grants against ~1027 expected.

The single-thread shortfall is the polling loop's own granularity (the partial token outstanding when the loop exits), not lost refill time — note it doesn't grow with contention, which is what actual drift would do.

Two real properties of monotonic worth knowing, in case one of them is what you were seeing:

- On Linux `time.monotonic()` is `CLOCK_MONOTONIC`, which does not advance while the machine is suspended. After a resume the bucket refills as if no time passed. That's the conservative direction (it under-grants, never over-grants), but if you want suspend time to count, `time.clock_gettime(time.CLOCK_BOOTTIME)` passed as `clock=` gives you that with no other change.
- The clock is read under the lock, so a thread that blocks between reading the clock and spending can't skew the balance.

If you're seeing a real rate deviation in a running system, tell me what you measured — observed grants against expected over what window — and I'll trace it. It's more likely to be several bucket instances, or a bucket rebuilt per request (each one starts full, at `:39`), than the refill arithmetic.
