# Managed database or your own

The decision comes down to what your team's time is worth and how much control the workload actually requires.

## What managed buys

RDS, Cloud SQL, and their peers handle backups, failover, patching, and point-in-time recovery. Failover happens in a minute or two without anyone paged. Minor version upgrades land in a maintenance window you pick, and you get metrics, slow query logs, and read replicas from a console form. The bill runs roughly two to three times the equivalent compute cost, sometimes more once you add storage IOPS and cross-AZ replication traffic.

## What you give up

Superuser access, mostly. No custom extensions outside the provider's approved list, no kernel tuning, no shared memory adjustments, no filesystem choices. Debugging a stall means reading whatever the provider exposes; you cannot strace the process. Major version upgrades follow the provider's schedule, and deprecation notices arrive whether the timing suits you or not.

## When self-hosting wins

Run your own when you need an extension the provider does not offer, when your data volume makes managed pricing absurd (tens of terabytes with steady load), or when you already employ people who know Postgres internals and have on-call coverage. Self-hosting costs about one engineer's ongoing attention: backup verification, replication monitoring, capacity planning, security patches. If nobody owns that, the database will eventually be down at 3am with no tested restore path.

## The practical answer

Start managed. Move off it when a specific constraint forces the question, and you can name the constraint out loud to the people paying for the migration.
