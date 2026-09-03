Managed database or self-hosted: choosing between them

A managed service like RDS, Cloud SQL, or Atlas takes over provisioning, patching, backups, and failover. You configure instance size, storage, and replication topology through an API or console, and the provider handles the operating system, the database engine's minor version updates, and disk-level redundancy. The tradeoff is control: you cannot install arbitrary extensions on most managed Postgres offerings, you cannot tune kernel parameters, and you pay a premium — often 20-50% over raw compute cost — for that operational transfer.

Running your own database means installing the engine on infrastructure you control, whether that is bare metal, a VM, or a container. You choose the exact version, every extension, and every configuration flag. You also own every 3am page: disk fills up, replication lags, a kernel update breaks the storage driver. A team without a dedicated database administrator will spend real engineering hours on this that a managed service absorbs.

The decision usually comes down to two questions. First, does the workload need something the managed provider does not expose — a specific extension, a nonstandard replication setup, a storage engine the provider does not support? Second, does the team have the on-call capacity to handle database incidents at 3am without burning out the two engineers who understand Postgres internals?

For most teams under 50 engineers, a managed service is the right default: the cost premium is smaller than one incident response. Self-hosting makes sense past a certain scale, where the managed provider's markup on compute exceeds the fully loaded cost of a database team, or where the workload has hard requirements the provider cannot meet.
