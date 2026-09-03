Choosing a Database: Managed or Self-Hosted

A managed database service (RDS, Cloud SQL, Atlas, PlanetScale) runs the database on infrastructure the provider controls, and hands you a connection string in exchange for a markup on compute and storage. Self-hosting means you provision the instance, install the engine, and own every layer above the hardware.

The case for managed is operational. Failover, patching, backups, and replication come configured by default, and the provider's on-call team has seen your failure modes before. Point-in-time recovery, read replicas, and encryption at rest are checkboxes instead of projects. For a small team without dedicated database expertise, this can save weeks of setup and prevent the kind of 3am incident nobody wants to debug from a runbook.

The case for self-hosting is control and cost at scale. You choose the exact engine version, tune parameters the provider hides, and run extensions the managed platform hasn't approved. At high, sustained resource usage, the markup on managed compute stops making sense, and running the database on your own hardware or reserved instances is cheaper than the equivalent managed tier. You also avoid provider-specific limits — connection caps, storage ceilings, maintenance windows that arrive on their schedule rather than yours.

The decision comes down to two questions. First, does your team have the expertise and headcount to own on-call for a database, including replication failures and corrupted backups? Second, is your workload large or unusual enough that the managed markup outweighs the operational savings?

If you answer no to the first question, choose managed regardless of cost. Database outages are unforgiving, and inexperienced on-call makes them worse, not cheaper.
