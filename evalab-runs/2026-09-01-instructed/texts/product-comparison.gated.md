# Managed database or your own?

Start managed. The interesting question is when that stops being right.

What you buy from RDS, Cloud SQL, or Neon isn't the database — it's the same Postgres you'd install yourself. What you're paying for is the on-call rotation. Automated failover, point-in-time recovery you can actually test, minor-version patching, and a support contract someone answers at 3 a.m. For six people shipping a product, that's the cheapest headcount available. The bill is where it turns. A managed 16-vCPU instance with 2 TB of provisioned IOPS runs roughly 3–5× the equivalent EC2 box plus EBS, with storage and IO marked up hardest. Once the database costs more per month than an SRE, the arithmetic flips — assuming you then hire the SRE, which most teams don't.

Control is the other axis. Managed providers withhold superuser, which rules out some extensions, most `shared_preload_libraries` changes, kernel and filesystem tuning, and running `pg_upgrade` on your own schedule. If you need `pg_cron` alongside a patched `pgvector` and a pinned glibc for collation stability, you will spend your quarter arguing with the platform.

Self-hosting means owning backups you have restored, not backups you have configured. Owning replication-lag alerts. Owning a failover drill someone actually ran last quarter.

Most self-hosted database outages trace back to a backup nobody tested, so treat that as the real entry fee rather than the hardware. Roughly, under 1 TB and under 10k writes/sec, stay managed — the markup is smaller than the distraction. Past that, or with hard extension requirements, price the alternative honestly, including the person who carries the pager.
