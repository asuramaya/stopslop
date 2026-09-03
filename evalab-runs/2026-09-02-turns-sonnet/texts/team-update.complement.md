September update

Migration's done. Every worker's on the new job-runner, and we killed the old queue-worker container on the 28th. Errors dropped by half in the first week since the new system retries failed jobs instead of dropping them.

Priya Nair joins October 1st on platform. Marcus Webb started last week, already working through onboarding with the infra pair.

Reporting API slipped again, August 29th to September 19th to now September 26th. Duplicate rows show up when a report spans a timezone boundary, and the fix touches the same code we rewrote for the schema change. Priya and Marcus will pair with the API owner on it once Priya's ramped.

Thanks to Dana and Kwame for covering on-call this month.

Sorry about the second slip. Ping me with questions.
