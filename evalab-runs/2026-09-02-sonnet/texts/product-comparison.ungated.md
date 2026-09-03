# Managed vs. self-hosted: choosing a database

Every team running a database eventually asks whether to keep managing it themselves. The answer depends on where you want to spend engineering time.

A managed service — RDS, Cloud SQL, PlanetScale — takes over backups, patching, failover, and replication. You get a dashboard, an API, and an on-call rotation that isn't yours. The tradeoff is cost and control: managed instances run 30-50% more than equivalent raw compute, and you lose access to the filesystem, custom extensions, and kernel-level tuning. Vendor lock-in is real too — proprietary replication protocols and connection poolers make migration harder later.

Running your own database means full control over configuration, extensions, and hardware. A team with strong ops experience can tune for their exact workload and pay only for compute and storage. But someone has to own 3am pages, security patches, and disaster recovery testing. That's not a one-time cost — it's ongoing headcount.

The decision usually comes down to three questions. How many database engineers does the team already have? A five-person infra team with Postgres expertise loses little by self-hosting. A two-person startup loses weeks to the first replication incident. What's the compliance burden? Some regulated environments require infrastructure control that managed offerings don't provide. What's the actual scale? At small scale, managed pricing is a rounding error; at large scale, self-hosting can save real money.

Most teams start managed and reconsider only when the bill or the control limits start to hurt. That's the right default — the failure mode of self-hosting too early is worse than the failure mode of paying a premium you don't need yet.
