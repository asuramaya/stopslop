# Incident report: login latency spike

**Date:** 2026-09-01
**Window:** 14:05–14:32 UTC (27 minutes)
**Severity:** SEV-2

## Impact

Login p50 latency went from 40ms to 9s. Requests still returned 200s, so nothing failed outright, but a nine-second login is a broken login from the user's side. Most sessions in the window either timed out client-side or were abandoned.

## What happened

The 14:05 deploy carried a database migration that dropped an index. The migration was written against a schema review that did not account for the login query, which used that index for its lookup. Once it was gone, the planner fell back to a sequential scan.

The regression was live for 25 minutes before anyone saw it. Our alerting on the login path is bound to error rate, and error rate never moved: the query was slow, not failing. Detection came from a support ticket, not from monitoring. A rollback of the migration went out at 14:32 and latency returned to baseline within a minute.

## Contributing factors

- Migration review had no step for checking index usage against live query plans.
- The login SLO is defined on latency, but no alert enforces it. Error rate was standing in for health and does not cover this failure mode.
- No canary or latency check gates the deploy pipeline.

## Follow-ups

1. Add a p95 latency alert on the login endpoint, paging at 500ms sustained for two minutes. (Owner: platform, this week.)
2. Require an `EXPLAIN` diff against production query plans for any migration that drops or alters an index.
3. Hold deploys for five minutes on a latency canary before full rollout.
