# Managed database vs. self-hosted

## What you actually buy

A managed service (RDS, Cloud SQL, Neon, Planetscale) sells you the operational floor: automated backups with tested restores, failover that someone else has rehearsed, patch windows, and a pager that isn't yours. Running your own on EC2 or bare metal buys you control over every knob below the SQL layer — kernel parameters, filesystem, extension versions, replication topology, and the exact minor release you pinned after a regression.

## Cost

Managed Postgres typically runs 2–4x the raw compute price for the same instance class. That premium is roughly one part hardware markup, one part the DBA hours you no longer spend. If your team has a person who already knows autovacuum tuning and WAL archiving, the math shifts. If you'd be hiring for it, it doesn't.

## Where self-hosting wins

Extensions the provider won't install. Superuser access. Storage layouts the managed tier doesn't offer. Data residency in a region or facility with no managed option. Workloads where the per-IOPS pricing on managed storage becomes the dominant line item at scale — this bites hard above a few TB of hot data.

## Where managed wins

Point-in-time recovery you'll never have to build. Minor version upgrades that are a maintenance window instead of a project. Cross-AZ replicas behind one API call.

## A rough rule

Start managed. Move off it when a specific, named constraint forces the move — a cost line, an extension, a residency requirement — not because self-hosting feels more serious. The migration back out is far cheaper than the incident you'll have learning failover in production.
