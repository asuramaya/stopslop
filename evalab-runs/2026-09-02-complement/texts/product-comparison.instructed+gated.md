# Managed database or self-hosted

The decision comes down to what you want to spend engineering time on, and how much control you need over the layer underneath your data.

A managed service (RDS, Cloud SQL, Neon, PlanetScale) takes over provisioning, patching, backups, failover, and replica setup. You get a connection string and a console. The cost is roughly 2 to 3x the equivalent raw compute, and you inherit the provider's constraints: no superuser, a fixed list of allowed extensions, upgrade windows on their calendar, and version support that lags upstream by six to eighteen months.

Running your own means you own the whole stack. You choose the Postgres version the day it ships, install any extension, tune shared_buffers and the kernel to match your workload, and colocate the database with your application to cut network latency. You also own 3 a.m. failover, PITR testing, connection pooling, replication lag monitoring, and the security patch cycle. That is a standing commitment of roughly a quarter to a half of one engineer's time once you pass a few hundred gigabytes and any real availability target.

Pick managed if your team is under about fifteen engineers, your workload fits standard configuration, and nobody on staff has run a production database through a failure. Pick self-hosted if you have a database specialist already, your bill exceeds five figures a month, you need an extension the provider will not install, or regulatory constraints put the data in your own racks.

Plenty of teams split the difference, running managed for the primary transactional store and self-hosted for analytics replicas where the cost per terabyte dominates.
