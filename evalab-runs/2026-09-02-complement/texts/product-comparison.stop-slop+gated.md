Managed Database or Your Own

A managed service (RDS, Cloud SQL, Neon) charges two to four times raw compute price.

Run your own Postgres and you own the parts the sales demo skips: WAL archiving to object storage, quarterly restore drills, connection pooling under load, major-version upgrades that need a logical replication cutover, and enough kernel tuning to keep a checkpoint storm from stalling writes. Each costs an engineer a week to build and a day per quarter to keep working, and someone on your team carries the pager for the 3am failover the provider's on-call engineer would have handled while you slept. Price that salary against the markup before you sign.

The managed side costs you control. Amazon decides your extension list, so if you need pg_cron or a C extension you wrote, you file a ticket and wait a release cycle. The vendor keeps superuser, which means you cannot attach a debugger to a stuck backend. You inherit whatever recovery point objective they publish, and during an outage you refresh the same status page as their other customers.

Count your engineers first. Below ten, with nobody who owns the database, buy the managed service and spend the saved weeks on your product. Above fifty, with someone who reads query plans for a living, your own hardware pays for itself and you tune for your workload instead of the vendor's median customer.

The middle is harder to call. Start managed, keep schema and migrations portable, and check the bill each quarter. Leaving costs a weekend if you kept that door open, or a rewrite if you built on Aurora's storage semantics.
