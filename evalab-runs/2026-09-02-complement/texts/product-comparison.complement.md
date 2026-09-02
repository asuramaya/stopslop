# Managed Database vs. Self-Hosted

The choice comes down to what you want to spend engineering time on.

A managed service (RDS, Cloud SQL, Neon, PlanetScale) gives you provisioning, patching, backups, failover, and point-in-time recovery as configuration rather than code you maintain. You click a checkbox for a read replica. The provider's on-call handles a failed host at 3am. In exchange you pay roughly 2-4x the raw compute cost, you lose superuser access, and you inherit their upgrade calendar. Extensions are limited to an approved list, which bites the first time you need something the provider hasn't blessed.

Running your own means you own the whole stack: kernel tuning, filesystem choice, connection pooling, replication topology, backup verification. You can run any extension, pin any version, and colocate the database with your application to cut network latency. The hardware bill drops sharply, especially at scale on dedicated servers.

The cost that surprises people is not the setup. It's the ongoing operational load: someone must test restores, watch replication lag, plan major-version upgrades, and answer the page. Budget at least a part-time engineer with real database experience. If your team lacks that person, self-hosting is a decision to acquire one.

A rough heuristic: below a few terabytes and without a dedicated infrastructure team, take the managed service. Once your bill reaches five figures monthly, or you need control the provider won't grant, running your own starts to pay.

Many teams do both, keeping the primary transactional store managed and self-hosting analytics replicas where downtime costs little.
