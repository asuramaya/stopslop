# Managed Database vs. Self-Hosted

A managed database service (RDS, Cloud SQL, Atlas, PlanetScale) handles provisioning, patching, backups, and failover. Running your own means owning every layer instead — the OS, the database engine, replication, monitoring, and the 3am page when a disk fills up.

Cost shifts, it does not disappear. Managed services charge a premium over raw compute, and that premium buys engineering time. A team with no dedicated DBA trades a visible bill for an invisible one when it self-hosts: hours spent on upgrades, tuning, and incident response.

Scale changes the calculus. At small scale, the trade favors managed, since the engineering hours saved outweigh the premium paid. At large scale, with predictable workloads and staff who already know the engine cold, self-hosting can cut costs meaningfully.

Control is the real axis. Self-hosting gives the exact version, extensions, and kernel-level tuning a team wants, useful for unusual workloads like custom extensions, exotic replication topologies, or hardware-specific tuning. Managed services restrict a team to what the provider supports, in exchange for tested upgrade paths and automated failover the team did not have to build.

Compliance and portability matter too. Some regulatory environments require full control over where data sits and who can touch the underlying hardware, a case for self-hosting. Locking into a provider's managed flavor of Postgres or MySQL can add migration friction later, since proprietary extensions and tooling do not always port cleanly. Choose managed by default unless a specific reason says otherwise: a DBA on staff, an unusual technical requirement, or a compliance mandate. Without that reason, the failure mode for self-hosting is a database that works until the day it does not.
