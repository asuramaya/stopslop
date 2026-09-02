# Incident Report: Login Latency Spike, 14:05–14:32 UTC

## Summary

A deploy at 14:05 UTC included a database migration that dropped an index the login query depends on. Login latency rose from 40ms to 9s. The degradation lasted 27 minutes. A rollback at 14:32 UTC restored normal latency.

## Timeline

- **14:05** — Deploy went out. The migration dropped the index.
- **14:05–14:30** — Logins succeeded, but each request took roughly 9 seconds. No alert fired.
- **14:30** — An engineer saw the latency graph during unrelated work and raised the alarm.
- **14:32** — The on-call engineer rolled back the migration. Latency returned to 40ms within a minute.

## Impact

For 27 minutes, every user who signed in waited about 9 seconds. Some clients timed out and retried, which added load to the same slow query. No data was lost and no request returned an error.

## Why detection took 25 minutes

The login alert watches error rate only. The dropped index made the query slow, not broken, so the error rate stayed flat and nothing paged the on-call engineer. Detection depended on a person who happened to look at a dashboard.

## Root cause

The migration removed an index that the author believed was unused. The team reviewed the migration, but nobody checked the index against live query plans before the merge.

## Actions

1. Add a latency alert on the login endpoint. Page when p95 goes above 500ms for two minutes.
2. Require every migration that drops an index to cite query-plan evidence in the pull request.
3. Audit the remaining critical endpoints for alerts that cover error rate but not latency.
