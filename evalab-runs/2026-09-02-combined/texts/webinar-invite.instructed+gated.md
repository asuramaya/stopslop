## Webinar on finding the query that's costing you Tuesday nights

Most database slowdowns don't announce themselves. A report that took four seconds in March takes ninety in September, and by then three teams have built workarounds around it.

This session walks through diagnosis on a live Postgres instance with about 40 million rows of order data. We start from the symptom — a checkout endpoint at p99 of 2.1 seconds — and work backward through `pg_stat_statements`, an EXPLAIN ANALYZE plan, and the index that was never used because of a type mismatch in the join condition.

Topics covered:

1. Reading an execution plan without guessing which node matters
2. When a composite index beats two single-column ones, and when it doesn't
3. Connection pooling limits and why raising max_connections usually makes things worse
4. Vacuum, bloat, and the maintenance window nobody scheduled

Bring your own slow query. The last twenty minutes are open, and we'll take as many as we can get through.

Led by Priya Raghunathan, who spent six years on the database team at Shopify and now consults on migrations.

Thursday, October 9, 1:00 pm ET. Ninety minutes. Recording goes out to everyone registered, whether or not you attend.

Register at [link].
