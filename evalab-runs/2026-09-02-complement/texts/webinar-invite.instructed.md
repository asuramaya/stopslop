## Your queries are slow. Come find out why.

A live 60-minute session on database performance tuning, Thursday 18 September, 15:00 UTC.

Most slow-query complaints trace back to a handful of causes: a missing composite index, a query planner working from stale statistics, an N+1 pattern in the ORM layer, or a connection pool sized for a load that no longer exists. We will walk through each one against a Postgres instance carrying about 40 million rows, with the query plans on screen.

What you leave with: a method for reading EXPLAIN ANALYZE output without guessing, three index strategies and the write cost each one carries, and a checklist for deciding whether the fix belongs in the query, the schema, or the hardware budget.

The second half is open Q&A. Bring a slow query and the plan output, and we will take as many as the hour allows.

Presented by [speaker name, title], who has spent [n] years on production database work at [company].

This suits backend engineers, data engineers, and anyone who has been handed an on-call page about p99 latency. Some SQL experience assumed; no prior tuning experience needed.

Registration is free. Recording goes out to registrants within 48 hours.

[Register]
