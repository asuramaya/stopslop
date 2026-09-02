## Managed Postgres vs. running it yourself

The decision isn't about cost, though that's where most teams start. A db.r6g.2xlarge on RDS with Multi-AZ runs roughly triple the EC2 sticker price for the same instance. Then someone does the math on a self-hosted equivalent, forgets to price a second on-call engineer, and declares victory.

Here's the actual tradeoff. Managed services sell you *ownership of the boring parts*: minor-version patching, base backups with PITR, a failover that takes 60–120 seconds without anyone waking up. You pay for that in ceilings. No superuser. No arbitrary extensions — RDS ships a fixed allowlist, so if you need `pg_partman` at a version they haven't blessed, you're filing a support ticket instead of running `CREATE EXTENSION`. Tuning `shared_buffers` past their parameter group defaults, same story.

Self-hosting gives all of that back, and hands you the pager. You now own WAL archiving, replication lag alerting, connection pooling, disk-full incidents at 3am, and the major-version upgrade that nobody wants to schedule. Patroni and pgBackRest are good software. They are still software you have to operate.

So I run it myself when the database *is* the product — you're doing multi-terabyte analytics, custom extensions, replication topologies your provider won't express. Otherwise go managed, and spend the saved headcount on something a vendor can't sell you.

Price one thing early, though. Egress and cross-AZ transfer on managed services can quietly exceed the instance cost for write-heavy, replicated workloads. Check that before you sign anything.
