# Choosing between a managed database and your own

The choice is not about capability. Postgres is Postgres either way. It is about which failures you want to own.

A managed service (RDS, Cloud SQL, Neon, PlanetScale) sells you an on-call rotation. Backups run without anyone writing them. Minor version upgrades happen in a window you pick. When the underlying host dies at 3am, someone else gets paged and a replica gets promoted. You pay roughly two to four times the raw compute cost for that, and you accept a smaller surface: no superuser, a curated extension list, limits on kernel and filesystem tuning.

Running your own is the opposite trade. Any extension you want, arbitrary tuning, colocation with the app, and a bill that is mostly instance-hours. You also inherit the work, which means point-in-time recovery you have tested by actually restoring, connection pooling, failover that does not split-brain, and someone who knows what to do when autovacuum falls behind on a 2TB table.

The cost crossover arrives later than people expect. Below roughly $2k/month of managed spend, one DBA's salary dwarfs the premium. Above that, with steady load, self-hosting starts to pencil out, assuming you already have the people.

Four questions decide it:

- Does anyone on the team want to operate databases? Not "can" — want.
- Have you hit an extension or a config knob your provider withholds?
- What is your real RTO, and have you proven you can meet it?
- Is your load steady or spiky?

Default to managed. Leave it when you have a named reason and the staff behind it.
