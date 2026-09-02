Login latency incident — 2 September 2026

At 14:05 UTC we deployed a database migration that dropped an index the login query depends on. Without it the query fell back to a sequential scan, and login latency went from about 40ms to roughly 9 seconds.

Logins still worked, which is why nothing paged. Our alerts on the login path watch error rate only, and the error rate never moved. Requests were slow, not broken, so the monitors had nothing to say. We found out 25 minutes in, from user reports rather than from our own systems.

A rollback at 14:32 restored the index, and latency dropped back to baseline within a minute. Total user-visible impact was 27 minutes of a login flow slow enough to count as broken.

Two things went wrong. Reviewers treated the migration as a schema cleanup, and the index looked unused because the review only checked for explicit references in application code. The login query picks it up through the ORM's generated SQL, so a grep found nothing. And our alerts treat "returns 200" as healthy, which leaves a whole class of degradation invisible.

Follow-ups:

- Add a latency alert on the login endpoint, p95 over 500ms for two minutes. Owner: platform. This week.
- Require `pg_stat_user_indexes` scan counts in the review checklist before any migration that drops an index, instead of a code search. Owner: data.
- Audit the rest of our alerts for the same gap. Anywhere we alert on errors and not on latency is a candidate for the same silent failure.
