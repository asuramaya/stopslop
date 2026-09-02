**Why your p99 is lying to you**
Thursday, September 18, 11am PT. Fifty minutes, then questions until we run out.

Most tuning advice starts at the index. We're starting somewhere less fun, the place where a query that runs in 4ms on your laptop takes 900ms under load while sixty connections fight over the same buffer pool.

Ana Petrić has spent eight years running Postgres and MySQL fleets at companies that don't get to schedule downtime. She'll walk through four incidents from the past year and what the fix actually was, including the two where the fix was "delete this index."

Covered: reading EXPLAIN ANALYZE without fooling yourself, connection pool sizing (the right number is smaller than you want it to be), the point where a covering index stops paying for itself, and why lazy loading in your ORM shows up in the metrics as a network problem.

Bring a slow query. Paste it in the chat, we'll pull a few apart live.

No slides explaining what a database is. This assumes you've written SQL and stared at a query plan before, even badly.

Free, and the recording goes to everyone who registers. The live Q&A is the part worth showing up for.

[Save my seat]
