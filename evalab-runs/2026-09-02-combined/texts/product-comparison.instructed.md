# Managed database vs. self-hosted

The choice comes down to who absorbs the operational failure modes, and what you pay for that transfer.

A managed service (RDS, Cloud SQL, Neon, Planetscale) sells you a smaller surface area. Backups run without a cron job you forgot to test. Minor version patches land in a maintenance window. Failover to a standby is a configuration checkbox rather than a Patroni cluster you have to understand at 3am. The tradeoff is control: you lose superuser, so extensions outside the provider's allowlist are unavailable, and `shared_preload_libraries` is whatever the vendor decided. You also lose the ability to diagnose below the API — no strace on the postmaster, no reading the actual disk layout.

Self-hosting gives all of that back and costs roughly 3-5x less per GB of RAM at comparable specs. On a single EC2 instance with local NVMe, you get IOPS that provisioned EBS charges heavily for. But the cost is not the instance, it is the engineer-hours. Someone has to own PITR testing, connection pooling, replication lag alerting, and OS-level upgrades. If that person leaves, the knowledge often leaves with them.

A practical split: managed until your database bill exceeds roughly the loaded cost of half a DBA, or until you hit a hard technical wall — a custom extension, a replication topology the vendor won't allow, a latency floor you can't reach across their network. Below that line, the arithmetic favors renting.

One asymmetry worth weighing: migrating from managed to self-hosted is a weekend of `pg_dump` and DNS. Going the other direction after three years of accumulated custom tuning is a quarter of work.
