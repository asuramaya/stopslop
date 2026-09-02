# Managed Postgres or Your Own Box

The honest version of this decision: you're not choosing between databases. You're choosing which failure modes you want to own at 3am.

Run RDS or Cloud SQL and you get backups, failover, patching, and point-in-time recovery without writing a line of it yourself. Real value. The catch is that you also inherit the provider's opinions. No superuser. Extensions limited to whatever's on the allowlist, which is why half the pgvector adoption stories from 2023 start with someone waiting on a support ticket. Version upgrades happen on their calendar, not yours, and the maintenance window will eventually land somewhere inconvenient.

Self-hosting flips all of that. You get root, any extension you can compile, kernel tuning, and the ability to put WAL on separate NVMe. You also get to write the failover logic. Patroni plus etcd works well, though "works well" here means someone on your team understands quorum behavior during a network partition, and can debug it while the site is down.

Cost is where the argument usually happens, and it's usually argued badly. Managed runs roughly 2-4x the raw compute, but if that gap is smaller than a fraction of a DBA salary, you've answered the question.

My read: default to managed. Go self-hosted when you have a specific, nameable requirement the provider blocks (a custom extension, a replication topology, sub-millisecond p99 that needs local disk) or when your scale makes the markup absurd.

"We want more control" isn't a requirement. It's a preference, and it costs about one engineer.
