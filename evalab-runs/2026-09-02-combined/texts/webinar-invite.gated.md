**Your slowest query is not the one you think it is**

*A live webinar on database performance tuning · [Date] · [Time] · 60 minutes*

Most teams tune the query that shows up in the incident report. Meanwhile the real cost is a 4 ms lookup that runs 90,000 times a request cycle, buried under an ORM that swore it was batching.

We're spending an hour on the boring parts that actually move p99 latency. Working through real EXPLAIN output, with a live database, and enough time to argue about it.

What we'll cover:

- Reading an execution plan without guessing — where the planner's row estimate goes wrong and how to tell
- Index design once you get past the single-column reflex, from composite ordering to covering indexes to the ones you can drop today
- Connection pooling math, and why raising `max_connections` usually makes things worse
- Diagnosing lock contention while it's happening, not from yesterday's logs

Bring a plan you don't understand. We'll take audience submissions in the last twenty minutes and work through as many as we can.

Hosted by [Name], [Title], who has spent [N] years on the wrong end of a 3 a.m. page.

Free. Recorded, and the recording goes to everyone who registers.

[Register →]
