# Managed vs. self-hosted Postgres

You are not choosing between "easy" and "hard." You are choosing which failures you want to own.

**What managed buys you.** RDS, Cloud SQL, Neon and friends handle the work nobody puts on a résumé — minor-version patching, backup verification, failover plumbing, the replica that silently fell behind. A managed provider will do a point-in-time restore correctly at 3 a.m. Your on-call engineer, on their fourth week of interrupted sleep, might not.

**What it costs.** Roughly 2–4x the raw compute price, and you lose the superuser bit. No custom extensions outside the vendor's allowlist, limited control over `shared_buffers` and the autovacuum knobs, and a hard ceiling on instance size that you will hit eventually. When replication lag spikes for no visible reason, your debugging tool is a support ticket.

**When self-hosting wins.** You need an extension the vendor won't ship — TimescaleDB, a custom C function, `pg_partman` at a version they don't carry. Or your data volume makes the markup absurd: at 40 TB, the difference funds two full-time DBAs with room left over. Or a regulator requires the disks be yours.

**The rule of thumb.** Under ~5 TB with fewer than three engineers who genuinely know Postgres internals, take the managed offering and spend the saved attention on your schema — which is where your actual performance problems live anyway. Above that, or with a real DBA on staff, run it yourself.

Either way, test your restores. Nobody's backups work until someone proves it.
