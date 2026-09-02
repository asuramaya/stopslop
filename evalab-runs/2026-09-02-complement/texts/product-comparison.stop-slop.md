A managed Postgres on RDS runs roughly 1.8x the price of the same instance class on EC2, and closer to 3x once you turn on Multi-AZ. You are paying for a standby you never provision, a backup schedule you never write, and a minor-version upgrade path someone at AWS tests before it reaches you.

What you surrender is root. You cannot load an arbitrary extension, install a custom C function, or read the file system under the data directory. RDS exposes a subset of `postgresql.conf` through parameter groups, so tuning stops where Amazon decided it stops. Teams that need `pg_cron` on a version AWS has not certified, or that want to pin 15.4 for two more quarters, hit this wall in month three.

Running your own buys those knobs back and hands you an obligation. Someone carries the pager. Someone restores last Tuesday's backup into a scratch instance to prove the backup works, because an untested backup is a hypothesis. Budget half an engineer's time per quarter for patching, replication lag, and the vacuum tuning nobody wants to own.

The threshold most teams find: below about 500 GB and 5,000 transactions per second, the managed bill is smaller than the salary line it replaces. Above that, and with a platform team already on rotation, self-hosting starts to pay.

Two questions settle it. Do you need database internals your provider blocks? Do you have a named on-call owner who has done a restore drill this year? Answer no to both and take the managed service.
