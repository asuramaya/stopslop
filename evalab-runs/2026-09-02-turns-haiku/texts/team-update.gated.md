August Engineering Update

Database migration shipped early—Infrastructure ran the parallel reads cleanly and we're fully off the legacy schema.

Sarah and Marcus are starting this week. Sarah's joining Backend from [Company]'s payments team, Marcus is our new Frontend hire with five years of React experience. Give their PRs real attention the first few weeks.

The API latency work slipped again, now mid-November. Turns out the reporting schema was the bottleneck, not the queries. We should've fixed that first before optimizing. We're tackling it properly now and pulling someone from Platform next sprint to keep it moving. Won't hit our Q3 target but won't block shipping.

Thanks to James and Priya for covering on-call during the migration.

Syncs start back Monday. Let us know early if something's blocking you.
