# Your queries are slow. Come find out why.

Join us Thursday, October 9 at 1pm ET for two hours on database performance tuning with Priya Nadkarni, who spent six years on the query optimizer team at Percona.

This is a working session, not a survey of best practices. We start with a Postgres instance carrying 40 million rows and a checkout query that takes 4.2 seconds, and we get it under 100ms while you watch. Then we do it again with a different failure mode: a report query that is fast on staging and falls over in production, where the table statistics are eight weeks stale and the planner picks a nested loop over 2 million rows.

What we cover:

1. Reading EXPLAIN ANALYZE output without guessing which number matters
2. Index selection when three candidate indexes all look reasonable
3. Why your connection pool settings may be the actual bottleneck
4. How to see lock contention, prove it is the cause, and fix it
5. When to stop tuning and change the schema instead

Bring a slow query. The last 30 minutes are open, and Priya will take live submissions from the chat.

Attendees from the June session sent in 61 queries. We got through 11.

Free to attend. Recording goes out to everyone who registers, whether or not you make it live.

[Save your seat]
