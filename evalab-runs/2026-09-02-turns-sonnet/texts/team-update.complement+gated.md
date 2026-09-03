September update

Finished the Postgres migration this month, 12 to 15, over a weekend window. Replicas cut over first, write path followed once replication lag sat at zero for six hours. Ran a rollback drill mid-week just in case; didn't need it.

Priya Nair (platform) and Jamal Reyes (infra) joined the team, onboarding this week and pairing with the team. Search reindexing slipped again, now targeting September 19, because the events service schema change also dropped two fields our new mapping layer needs for backfill, so the rewrite needs another pass. Asked the events team to hold that schema until we ship. CI got four minutes faster after parallelizing tests, and billing held up fine through last week's traffic spike. Thanks to Marcus and Dana for covering on-call during the cutover.

We'll ship reindexing, kick off the on-call rotation redesign, and get Priya and Jamal onto their first solo tickets next month.
