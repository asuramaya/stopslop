Draft is at `/tmp/dbpage.md` (260 words, passes `stopslop.py lint --ruleset slopwatch` clean):

---

# Running Postgres yourself, or paying someone else to

The choice usually comes down to what your team's time is worth and how unusual your workload is.

A managed service — RDS, Cloud SQL, Neon, whichever — sells you a database that already has backups, point-in-time recovery, failover, minor-version patching, and a monitoring dashboard. It also takes away the knobs that would let you break those things. If your workload is ordinary (a few hundred gigabytes, read-heavy, latency budgeted in tens of milliseconds) you will probably never miss them, and the on-call rotation you don't have to staff is worth more than the price premium, which tends to run two to four times raw compute.

Running it yourself buys the knobs back. You pick the kernel, the filesystem, the extensions, the pooler, the exact minor version, and the week it changes. That matters when you need an extension the provider hasn't blessed (pgvector was late everywhere; TimescaleDB still isn't on RDS), when you're pushing the hardware hard enough that NVMe layout and huge pages show up in your p99, or when data-residency rules make a third-party operator awkward to explain to an auditor.

The cost you take on is not the install. It's the second year: someone has to test the restore, watch replication lag at 3am, plan the major-version upgrade, and still work here when it happens. Teams underestimate that part consistently.

A rough rule. Self-host when the database is the hard part of your product, and someone on staff already knows why autovacuum is falling behind. Otherwise pay.

---

I wrote it around Postgres specifically because a generic "managed database" comparison can only trade in abstractions — the concrete claims (extension availability, the price multiple, autovacuum) are what make it useful to someone actually choosing. Say the word if you want it genericized across engines, or dropped into a file in `docs/`.
