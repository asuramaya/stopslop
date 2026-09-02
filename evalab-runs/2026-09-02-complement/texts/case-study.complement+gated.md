Northwind Freight runs a logistics platform for regional carriers in the Midwest. Two years ago its engineering team of 34 shipped on a fixed schedule: one release every third Thursday, cut manually, verified by a four-hour smoke test that two people ran by hand. Anything that missed the cut waited three weeks.

The team adopted Harbor CD in March 2024. The first six months went into work that had nothing to do with the platform itself. They replaced 900 manual test steps with an automated suite, split a single deployable into eleven services, and moved database migrations behind feature flags so a schema change could land a week before the code that used it. None of that was in the original six-week rollout estimate.

Deploy frequency went from 17 releases a year to roughly 40 a week.

Median lead time from merge to production dropped from 19 days to 51 minutes. Change failure rate rose slightly in the first quarter, from 4% to 6%, then settled at 3% once the team added automated rollback on error-rate regression. The number the finance team cares about is a different one. Northwind's carrier onboarding flow used to take six weeks of back-and-forth, because each requested change waited for the next release train, and carriers routinely asked for two or three changes before signing. It now takes nine days. Sales closed 22 additional carrier contracts in 2025 that the old cadence would have pushed into the following year.

"We stopped treating a deploy as an event," said Priya Raghavan, VP of Engineering. "Nobody schedules one. Nobody watches one. My on-call rotation is quieter than it was when we shipped 17 times a year."
