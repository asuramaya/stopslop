# Managed Database vs. Self-Hosted

The trade is money for attention. A managed service (RDS, Cloud SQL, Neon, PlanetScale) charges roughly two to four times the raw compute cost, and in exchange takes over the work that wakes people at 3 a.m.: failover, backups, patching, replica promotion. Running it yourself costs less per gigabyte and more per engineer.

**What you actually get.** Automated backups with tested point-in-time recovery. Failover that has been exercised on someone else's fleet, not just in your runbook. Minor-version patching on a schedule you can defer but not ignore.

**What you give up.** Superuser. No custom extensions outside the provider's list, no kernel tuning, no `pg_stat_statements` variants they haven't blessed. Connection limits are set by instance class, so you may need PgBouncer anyway. And your storage layer becomes a black box: when p99 latency doubles, you file a ticket instead of reading `iostat`.

**Cost crossover.** Managed wins until you're spending five figures a month, at which point a dedicated DBA becomes cheaper than the markup. Egress fees and cross-AZ replication traffic are where the bill surprises people.

**A decision rule.** Self-host if you have someone on staff who has restored a production database from backup under time pressure, and you need control the provider won't give you. Otherwise use managed, and spend the saved headcount on your application.

Migration between the two is not symmetric. Moving onto a managed service is a dump and restore. Moving off means rebuilding the operational muscle you stopped using.
