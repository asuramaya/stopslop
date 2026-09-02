# Managed Database or Your Own

Pick the managed service when your team is small and your database is boring. RDS, Cloud SQL, and Neon handle backups, failover, minor version patches, and point-in-time recovery. You pay roughly 2-4x the raw compute cost for that. A db.r6g.xlarge on RDS runs about $380/month against $180 for the equivalent EC2 instance, before storage and IOPS.

Run your own when you need something the provider blocks. RDS won't give you superuser, so you can't install arbitrary extensions, tune shared_preload_libraries freely, or run pg_repack without waiting for AWS to bless it. If you need Citus, TimescaleDB's community features on a managed Postgres, or a custom locale, you build it yourself.

The hidden cost of self-hosting is the pager. Someone on your team owns 3am disk-full alerts, replication lag, and the failover that didn't fire. Budget a quarter of an engineer's time at steady state, more during the first six months while you write the runbooks. Two engineers who both understand your replication topology is the real minimum, since one of them takes vacations.

Scale changes the math. Below 500GB and a few thousand QPS, managed wins on total cost including salary. Past a few terabytes with heavy write throughput, the managed premium becomes real money and self-hosting starts to pay for the operational headcount.

A middle path exists: run Postgres yourself on dedicated hardware, but buy support from Percona or EDB. You keep root, they take the 3am call.
