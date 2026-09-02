# Managed database or your own

The decision is rarely about the database. It is about who gets paged at 3 a.m. and what that hour is worth to you.

## What you buy

A managed service (RDS, Cloud SQL, Neon, Planetscale) sells you an operator. Backups run, minor versions get patched, failover is scripted and tested, and the storage layer is someone else's inventory problem. You give up root, kernel tuning, arbitrary extensions, and the ability to sit on a version past its support window. Costs land at roughly 2-4x the equivalent compute and storage, and egress pricing can dominate if your workload is read-heavy across zones.

Self-hosting gives you the whole surface. Any extension, any Postgres version, any filesystem, any replication topology. You can put the write-ahead log on local NVMe and cut p99 commit latency to a fraction of what network-attached storage gives you. You also own point-in-time recovery, connection pooling, upgrade rehearsals, and the runbook for a failed primary at 3 a.m.

## Where each one wins

Take managed when your team is under about eight engineers, when your database is one of many services rather than the product, or when compliance evidence is easier to buy than to produce. Take self-hosted when database performance is a competitive edge, when you need an extension no provider ships (TimescaleDB, pgvector at a specific version, Citus), or when your spend has grown past roughly one full-time salary of margin.

## The honest test

Ask who on your team has restored a production database from backup in the last six months. If the answer is no one, run managed until it is someone.
