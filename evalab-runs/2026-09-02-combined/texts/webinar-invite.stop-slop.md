Your queries are slow and you've already tried adding indexes.

Join us Thursday, October 8, at 1pm ET for a working session on database performance tuning. Ryan Okafor, who runs the platform team at Meridian Logistics, will walk through a Postgres instance he inherited last year: 400GB, 90 tables, and a checkout query that took eleven seconds at peak.

He will show you the sequence he used to bring it down to under 300 milliseconds. That includes reading an EXPLAIN ANALYZE plan without guessing, finding the difference between a query that needs an index and one that needs a rewrite, and deciding when connection pooling solves the problem you have versus the problem you think you have.

Bring a slow query. Ryan reserves the last twenty minutes to look at whatever attendees paste into the chat, and he tunes it live. Past sessions have run over because people keep asking.

You will leave with a written checklist for triaging a slow query, plus the pgbadger config Ryan uses to find the queries worth fixing first.

The session runs 60 minutes. We record it and send the link to everyone who registers, so sign up even if Thursday afternoon is bad for you.

Register below. Seats are limited to 200 so the live tuning stays useful.
