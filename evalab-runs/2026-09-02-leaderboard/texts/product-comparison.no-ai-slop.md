# Managed database or your own

A managed service (RDS, Cloud SQL, Neon) sells you an on-call rotation. You pay roughly two to three times the raw compute price, and in exchange you stop writing runbooks for failover, backup verification, minor-version upgrades, and disk expansion at 2 a.m.

Run your own and the hardware is cheap. A dedicated box with local NVMe gives you far better IOPS per dollar than network-attached storage, and single-digit-millisecond fsync latency instead of the 5 to 20ms you often see on EBS. If your workload is write-heavy or you are pushing past a few terabytes, that gap becomes the whole argument.

Self-hosting gets expensive in the second year. Someone has to test restores, patch CVEs, tune autovacuum before the tables bloat, and be reachable when the primary dies over a holiday. Half of one engineer's time is a fair estimate for a production cluster, and at loaded salary that usually exceeds the managed premium until your bill passes five figures a month.

Managed services also take things away. No superuser, no arbitrary extensions, limited access to the WAL stream, and upgrade windows the vendor picks. Check the extension list before you commit, since pgvector, TimescaleDB, and PostGIS support varies by provider and version.

Default to managed. Move off it when you can name the constraint pushing you off: a cost line you have measured, an extension you need, latency you have profiled, or a compliance rule about where the bytes live. "We could run it ourselves" is not one of those.
