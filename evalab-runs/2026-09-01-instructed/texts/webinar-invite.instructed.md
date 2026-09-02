**Your slowest query is not the one you think**

A live webinar on database performance tuning
Thursday, October 15, 11:00 a.m. ET · 60 minutes, 15 of them for questions

Most tuning work starts in the wrong place. Someone reports that the app feels slow, and the next four hours go into indexes on a table that was never the bottleneck. Meanwhile a single N+1 pattern in the ORM is issuing 800 round trips per page load.

This session walks through diagnosis in the order that actually narrows things down: read the wait events first, then the execution plan, then the schema. We'll work through three anonymized cases from production Postgres and MySQL systems — a query that got 40x faster after a composite index reversed its column order, a connection pool sized 10x too large, and a nightly job whose lock contention only appeared under concurrency.

You'll leave with a checklist you can run against your own database on Monday, plus the specific system views and EXPLAIN flags worth memorizing.

Led by Dana Okoro, who spent six years on database reliability at Stripe and now consults on query performance for mid-size SaaS teams.

Free to attend. Recording sent to everyone who registers, whether or not you make it live.

[Register]
