Subject

Your slowest query probably isn't the one you think

Most teams tune databases by folklore. Add an index. Bump the connection pool. Throw RAM at it and watch the p99 come down — until it creeps back two sprints later and nobody can say what changed. On [date], we're spending 60 minutes on the boring version of this problem: reading what the database is already telling you, in the order it tells you.

No war stories about the time someone dropped a table.

What we'll go through:

- Reading an `EXPLAIN ANALYZE` plan line by line, including the parts everyone skips
- Why the query in your slow log is often a symptom of a cheaper query running 40,000 times
- Index design past "put one on the foreign key" — covering indexes, column order, and when an index makes writes hurt more than it helps reads
- Connection pooling math, and the sizing mistake that turns a traffic spike into an outage

[Speaker name] has spent [N] years on Postgres and MySQL systems in the terabyte range, and will take live questions for the last 15 minutes.

Bring a plan you don't understand. Free, and recorded, so register even if the time doesn't work.

[Register →]
