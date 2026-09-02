## Managed database or your own

The pitch for a managed database — RDS, Cloud SQL, Neon, pick one — is that someone else is awake when the disk fills. You pay two or three times the cost of the underlying compute, and in exchange you stop thinking about minor-version upgrades, whether the backups actually restore, and failover at 3am.

For most teams that trade is correct. It's worth being precise about when it isn't.

Run your own when you need something the provider won't hand you: an extension outside the allowlist, superuser, filesystem and kernel tuning you've measured a reason for, or the new major version the week it ships rather than nine months later. Run your own when the pricing model turns against you. A 20TB table on provisioned IOPS gets expensive quickly, and past a certain size the managed premium stops looking like a service fee and starts looking like a salary — at which point hiring the DBA is the cheaper option, and a better one, because you get judgment along with the labor.

The mistake in the other direction is budgeting for the install. Setting up a replica pair is an afternoon. The cost lands in year three, when the person who tuned autovacuum has left, the runbook is stale, and nobody has tested a restore since the migration.

So the real question isn't technical capability. It's whether database operations is something your team will keep doing well after the people who set it up move on. If the answer is no, pay the premium.
