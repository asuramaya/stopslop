## Login latency spike incident report

**Duration:** 14:05–14:32 UTC (27 minutes)
**Impact:** Login p50 latency rose from 40ms to roughly 9 seconds. Logins still succeeded, so no errors were returned, but most users experienced the sign-in page as hung and many gave up and retried.

**What happened**

The 14:05 deploy included a database migration that dropped an index the login query depends on. The query fell back to a sequential scan. Latency jumped immediately.

Our paging alert for the auth service fires on error rate. Because the query returned correct results, just slowly, the error rate never moved and nothing paged. The problem surfaced at 14:30 when a support ticket about slow logins reached the on-call engineer. They correlated the timing with the deploy and rolled back at 14:32. Latency returned to baseline within a minute.

**Why the index was dropped**

The migration was written to clean up an index believed to be unused. The author checked index usage in a staging database, where login traffic is negligible, and saw near-zero reads. Production usage was never checked.

**Follow-ups**

1. Add latency alerts for the auth service. Page on p95 above 500ms for 2 minutes. Platform owns this. (It is the fix that matters. Error-rate-only coverage will miss this class of failure again.)
2. Require production index usage statistics in the review checklist for any migration that drops an index. Data owns this.
3. Review the other three indexes dropped in the same migration series and confirm they are genuinely unused.

**Not doing:** blocking deploys on migration review. The gap was monitoring, not process.
