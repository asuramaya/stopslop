Managed Postgres versus self-hosted, what changes and what doesn't

A managed service (RDS, Cloud SQL, Aiven, or similar) takes over backups, patching, failover, and storage expansion. You still own schema design, query performance, index strategy, and connection pooling. Nobody manages your data model for you.

The main trade is control for time. Self-hosting gives you the exact Postgres version and extension set you want, tunable parameters at the kernel and filesystem level, and no vendor markup on compute or storage. It also means you own the pager. A failed disk, a botched major-version upgrade, or a replication lag spike is now a 2am problem for your team, not a support ticket.

Cost comparisons that stop at instance pricing miss the real difference. A managed database costs 20-40% more than the equivalent raw compute, but that premium buys automated failover, point-in-time recovery, and security patching without a DBA on staff. If you already run one, self-hosting saves the premium. If you don't, the premium is cheaper than the incident.

Two factors decide it more than any other:

Compliance and data residency requirements sometimes force self-hosting, or a specific cloud region a managed provider doesn't offer.

Scale changes the math. At small to medium scale, managed wins almost every time: the operational burden outweighs the cost delta. Past a few hundred nodes or with unusual sharding requirements, some teams move to self-hosted for cost and control, but only with a dedicated infrastructure team already in place.

Default to managed. Move to self-hosted only when a specific, named constraint requires it, not because self-hosting feels like the more serious engineering choice.
