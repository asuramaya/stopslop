# Managed database or self-hosted: picking the trade

The decision is rarely about capability. Postgres is Postgres. What differs is who carries the operational weight, and what you pay for that.

## What a managed service actually buys

Backups run without you writing them. Point-in-time recovery exists on day one instead of the day after your first data loss. Minor version patches land during a maintenance window, failover to a standby is a config field, and someone else is paged at 3am when the disk fills.

The cost is roughly 2-4x the raw compute price, and it shows up in constraints you did not choose. No superuser. A fixed list of extensions. Parameters you cannot tune past the vendor's ceiling. If you need `pg_cron`, a custom C extension, or a nonstandard replication topology, check the allowlist before you commit.

## What self-hosting actually costs

Cheaper per gigabyte, and you keep every knob. The bill arrives as engineering time: someone has to own backup verification (not backup configuration), replica lag monitoring, connection pooling, upgrade rehearsals, and the security patches you now track yourself. Budget a quarter to half of an engineer's time for a production cluster that matters, and more during migrations.

## Where the line falls

Take managed when your database is under a few hundred gigabytes, your team has no dedicated DBA, and the workload is ordinary OLTP. Take self-hosted when the storage bill has grown past the salary of the person who would run it, when you need extensions or kernel tuning the vendor blocks, or when regulatory placement rules out the vendor's regions.

Migrating later is possible in both directions. It is a weekend of downtime you should plan for rather than discover.
