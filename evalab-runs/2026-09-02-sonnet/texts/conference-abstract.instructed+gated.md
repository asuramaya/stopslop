Breaking Up the Monolith: What Actually Happened

We ran one payments monolith for six years, then split it into 14 services. This talk covers the migration, including the parts that went wrong.

The rewrite started with the checkout path, the piece of code every team touched and no one owned. I walk through how we drew service boundaries around data ownership instead of team org charts, why our first attempt at a shared database between two independent services failed within a month, and how the strangler fig pattern let us route traffic gradually instead of committing to a big-bang cutover.

Latency was the real cost. A single checkout request went from 3 in-process function calls to 11 network hops across services, and our p99 doubled until we fixed it with request coalescing and a rethink of which calls needed to be synchronous. I show the before-and-after traces.

By the end, deploy frequency went from twice a week to about 40 times a day, and a single team's bug could no longer take down the entire platform. Attendees leave with a checklist for deciding whether their own system is ready for this migration, and three questions to ask before splitting a service.
