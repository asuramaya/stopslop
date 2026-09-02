## Incident report: login latency spike, 2026-09-02

**Summary.** A scheduled deploy at 14:05 UTC included a database migration that dropped an index the login query depends on. Login p50 latency rose from 40ms to about 9s. The team rolled back at 14:32, and latency returned to baseline within a minute.

**Timeline (UTC)**
- 14:05 — Deploy completes; migration drops the index.
- 14:05–14:30 — Logins succeed but take ~9s. No alert fires.
- 14:30 — Problem noticed and confirmed against the deploy.
- 14:32 — Rollback restores the index; latency recovers.

**Impact.** 27 minutes of degraded login. Requests completed, so no data was lost and no users were locked out, but sign-in was slow enough that many people almost certainly gave up or retried.

**Cause.** The migration removed an index that no longer appeared in the application schema but was still used by the login query's plan. Review looked at the migration on its own and did not check which queries depended on the index.

**Why detection took 25 minutes.** Login alerting is wired to error rate only. A query that gets 200x slower without failing produces no errors, so the alert stayed green for the whole window. Discovery came from a person watching a dashboard, not from paging.

**Follow-ups**
1. Add p95 and p99 latency alerts on the login path, with a page threshold well under 1s.
2. Require index drops to name the queries checked, with the query plan attached to the review.
3. Add a post-deploy latency comparison against the prior 30 minutes.
