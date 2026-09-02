# Managed database or self-hosted

The decision comes down to what you want to spend engineering time on, and how much control you need over the layer beneath your data.

## What the managed service buys

A managed service (RDS, Cloud SQL, Neon, PlanetScale) takes over backups, patching, failover, and point-in-time recovery. Failover is the important one. Getting automatic failover right on your own — heartbeats, fencing, quorum, split-brain avoidance — takes weeks to build and years to trust, because it fails rarely enough that you find the bugs during real incidents.

You pay for this in cash and in control. Managed instances typically run 2-4x the cost of equivalent compute, and you lose superuser: no custom C extensions, no kernel tuning, limited access to the filesystem where the data actually lives. When something goes wrong at 3am, your escalation path is a support ticket rather than a shell.

## What self-hosting buys

Self-hosting makes sense when your workload has a shape the managed tier prices badly: heavy write throughput, single instances in the multi-terabyte range, unusual extensions, or data-residency rules that no region satisfies. It also makes sense when you already have a team who runs stateful systems and an on-call rotation to absorb the pages. Be honest about that second condition, because it is the one people wave through. Self-hosting a database is not a one-time setup cost. It is a standing obligation to upgrade major versions, test restores, and watch replication lag.

## A rough rule

Under roughly 500GB and without a dedicated infrastructure team, take the managed service and spend the saved time elsewhere. Past that, or once the monthly bill exceeds an engineer's salary, run the numbers on self-hosting with a real headcount estimate attached.
