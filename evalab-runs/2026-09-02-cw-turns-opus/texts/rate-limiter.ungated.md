`rate_limiter.py` never used `time.time()`. The clock is `time.monotonic` — the default of the injectable `clock` parameter at line 14, stored as `self._clock` (line 23) and used in `_refill` (line 30), the initial `_updated` stamp (line 26), and the `acquire` deadline (lines 57, 66). There is no other time source in the file, and `grep -rn "time.time"` across the repo's Python only hits `routes_watch.py`, `harness.py`, and `history.py`, none of which the limiter touches.

So there is nothing to fix here, and no change made.

`_refill` also can't accumulate float drift: it recomputes from `elapsed = now - self._updated` and then sets `self._updated = now`, so each interval is measured once against the monotonic clock rather than summed from prior estimates.

If you are seeing drift under load in a real run, the likely candidates are elsewhere:

- Deliberate loss at the cap. `_refill` clamps to `capacity`, so a bucket that sits idle past its burst window discards the excess. Under bursty load that reads as "fewer tokens than rate × elapsed would predict." That is the spec you asked for, not a bug.
- Wall-clock stamps in the caller. If whatever measures the limiter's throughput uses `time.time()` (as `history.py:55` and `harness.py:371` do), an NTP step skews the *measurement*, not the bucket.
- `sleep` granularity in `acquire`. The OS overshoots short sleeps, so measured wait is a bit long. That makes it slower than the nominal rate, never faster.

If you have the numbers from the run that showed drift — expected versus observed rate, and how you timed it — send them and I'll trace where the gap comes from.
