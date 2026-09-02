Clean against the project's `slopwatch` gate. Here's the page (~265 words):

---

# Managed database or your own?

Both work. The choice is about where you want to spend attention.

A managed service (RDS, Cloud SQL, Neon, PlanetScale) sells you back the hours you would otherwise put into backups, failover, minor-version patching, and the 3 a.m. page when a disk fills. You get an endpoint and an SLA. In exchange you accept the provider's version cadence, their extension allowlist, and their pricing, often 2-4x the raw compute cost once you count cross-AZ traffic and provisioned IOPS. You also give up the superuser bit, which bites harder than people expect: no extensions outside the list, no filesystem, and some tuning knobs simply absent.

Running it yourself gets all of that back. You pick the Postgres version, install whatever extension you want, tune `shared_buffers` against your actual workload, and keep the data on hardware you chose. Cost per gigabyte drops a lot. The bill just arrives as headcount instead: someone has to own restore drills (a backup you have never restored is not a backup), replication lag, connection pooling, and the upgrade path.

So the deciding question is not technical. It is whether you have a person who wants this job and will still be there in two years. One competent DBA-ish engineer makes self-hosting cheaper and better than the managed option. Zero of them makes it a slow-motion outage with a two-year fuse.

A reasonable default: start managed. Move off when the bill passes an engineer's salary, or when the provider blocks something you actually need. Either direction is survivable with logical replication and a maintenance window. Plan the exit while you still have the choice.

---

I assumed Postgres for the concrete details since it's the common case on both sides — say the word if you want it engine-neutral or aimed at MySQL, and tell me if you'd like it written to a file rather than shown here.
