Your slowest query probably isn't the one you think

Every team has a dashboard that goes red at 2 a.m. Someone adds an index, the graph settles down for a month, and the same page times out again in June, because the index was never the problem. The real cause is usually sitting somewhere nobody thought to look, and it sits there until someone reads the plan instead of the graph.

On [DATE] at [TIME], [SPEAKER] walks through cutting p99 read latency on a 4 TB Postgres instance from 1.9 s to 210 ms, with no rewrite and no sharding.

What we'll cover:

- Reading an EXPLAIN ANALYZE plan without guessing
- Why the connection pool is your bottleneck more often than the disk is
- The three metrics that go bad before PagerDuty notices
- When to stop tuning and just buy hardware

Bring a slow query.

The last twenty minutes are open for live plan review, and [SPEAKER] will take whatever you paste into chat. Forty-five minutes total. Everyone who registers gets the recording.

[Register →]

The numbers (4 TB, 1.9 s → 210 ms, 45 minutes) are invented placeholders. Swap in your speaker's real case study, or the copy makes a promise the webinar can't keep. Same for Postgres and PagerDuty if your audience is on a different stack.
