**Database Performance Tuning: Finding the Query That's Eating Your Afternoon**

Your p99 latency doubled last month and nobody knows why. The dashboard says the database is healthy. Users say otherwise.

In this 60-minute session, [Speaker] tunes a slow database without guessing. We start with a real production Postgres instance and work from the symptom back to the cause.

What we cover:

- Reading an EXPLAIN ANALYZE plan and spotting the row estimate that's off by 1000x
- When an index earns its keep, when it sits unused, and how to tell which one you have
- Connection pool settings that cap your throughput before the query planner ever gets involved
- Lock contention, and why your writes stall at 2pm every weekday
- The three metrics worth alerting on, and the dozen that only generate noise

You'll leave with a checklist you can run against your own database that same afternoon.

Bring a slow query. We spend the last 15 minutes taking them from the audience and tuning them live, plan by plan.

**When:** [Date], [Time] [Timezone]
**Where:** Online. Join link goes out after you register.
**Cost:** Free. Recording sent to everyone who signs up, whether or not you attend.

[Register]
