# Managed database or roll your own?

The pitch for managed services — RDS, Cloud SQL, Neon — is that you stop paying an engineer to think about WAL archiving. That's real. Point-in-time recovery, minor-version patching, and failover to a standby all work on day one, and the pager for them belongs to someone else.

You pay for it twice. Once in money: a `db.r6g.xlarge` runs roughly 2–3x the EC2 instance underneath it. Once in control. You don't get superuser. Extensions come from a vendor allowlist, so `pg_cron` or TimescaleDB may simply not be available. Tuning happens through parameter groups, and major-version upgrades happen on the vendor's calendar rather than yours.

Self-hosting flips both. Any extension, any kernel parameter you want, at hardware prices. But the backups are now yours — and not just running `pg_basebackup`, but restoring from it quarterly to prove the restore actually works. Same for replication-lag alerts, connection pooling, disk-full pages at 3am, and the CVE that drops on a Friday.

The dividing line is honest headcount, not architecture. If nobody on the team has run production Postgres before, and nobody's job description says they're going to start, then self-hosting doesn't get you control. It gets you an unowned database with an untested backup script. Buy the managed one.

Go self-hosted when you already have a platform team, when the monthly bill has passed what an engineer costs, or when you need a capability the vendor won't permit. Those are the three cases. Outside them, the markup is cheaper than the staffing.

Most teams start managed and never need to leave.
