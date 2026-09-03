Cost flips at scale: a few large, stable instances running for years cost less self-managed than the same capacity rented monthly with a management fee attached — becomes:

Managed Postgres or Run Your Own

A managed service (RDS, Cloud SQL, Aurora) handles provisioning, patching, backups, and failover through an API or console. You pay a premium over raw compute, often 30-50%, for that operational layer. Self-hosting means running the database on your own instances, with your team writing the automation: backup scripts, replication setup, patch schedules, monitoring.

The case for managed is strongest when the team is small relative to the number of databases it runs. A two-person platform team supporting twenty microservices does not have time to test every minor-version patch across twenty clusters.

Managed failover, typically under a minute for RDS Multi-AZ, beats what most teams build themselves on the first attempt. But the case for self-hosting holds when you need control the managed layer doesn't expose: RDS Postgres caps you at whatever extensions AWS has allow-listed, no `pg_cron` on some versions, no custom C extensions ever. If your workload depends on a specific extension, tuned `shared_buffers` beyond what the console exposes, or storage hardware the provider doesn't offer, you negotiate with the platform instead of the database.

A few large, stable instances running for years cost less self-managed than the same capacity rented monthly with a management fee attached, so cost favors self-hosting at scale.

Aurora, Cloud SQL, and similar services offer a middle path worth checking before committing to either extreme. They let you self-manage schema and extensions while offloading storage and failover. That covers most of what drives teams toward full self-hosting, without the on-call burden of patching a fleet by hand.
