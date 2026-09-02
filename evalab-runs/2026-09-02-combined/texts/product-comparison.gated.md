# Managed database or your own

The question is not "which is better." It is which set of problems you would rather own.

A managed service takes the operational floor off your plate: provisioning, patching, backups, failover, point-in-time recovery. You get an endpoint and a control panel. The cost is a markup on hardware you could rent directly, often two to four times the raw compute price, plus limits on what you can touch. No superuser on most offerings. Extensions come from an approved list. Major version upgrades happen on the vendor's calendar, not yours, and when replication lags at 3am you file a ticket instead of reading a log.

Running it yourself inverts all of that. You choose the kernel, the filesystem, the connection pooler, the exact Postgres build with the extension nobody else supports. Storage costs what storage costs. But someone on your team now owns restore drills, monitoring, upgrade paths, and the pager. That is roughly a quarter to a half of an engineer's time once the system carries real traffic, and it is not the fun quarter.

Two questions usually settle it. The first asks whether you have someone who has restored a production database from backup under pressure, and whether they will still be here in a year. If not, buy the service. The second asks whether your database bill is large enough that a 3x markup exceeds the loaded cost of that engineer. Below roughly $10k a month it rarely is.

Most teams should buy first and revisit when the bill starts to hurt.
