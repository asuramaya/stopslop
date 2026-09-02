Passes the repo's `slopwatch` gate. ~255 words:

---

# Managed database, or your own box

The bill is the obvious difference and the least interesting one. RDS or Cloud SQL runs somewhere around two to three times the cost of an equivalent VM with a disk attached. Most teams see that multiplier, do the arithmetic, and stop there. That's the mistake.

What the markup actually buys is a pager rotation. The provider owns failover, minor-version patching, backup restores that have been tested, and the 3 a.m. alert when a volume fills. Self-host and someone on your team owns all of it, and that someone has to exist before the incident rather than after. If your on-call is one engineer who also ships features, you are not going to run a production database well. You will be on unpatched Postgres 14 in eighteen months, and you will find out during an audit.

The case for your own hardware is narrower than the forums suggest, and it is still real. You need an extension the provider blocks. You need superuser, or a replication topology the console will not draw. You are large enough that the multiplier is a salaried headcount, in which case hire the DBA. Or the data cannot legally leave a building you control.

Everything else is fashion. The default answer for a team under about thirty engineers is managed, and the honest reason is not technical: your database is not where your differentiation lives, and every hour spent on vacuum tuning is an hour not spent on the product.

---

The cost multiplier and the headcount threshold are round numbers from typical cloud pricing, not measured against your workload — swap in real figures if this ships anywhere. Say the word and I'll drop it into a file in the repo.
