# Northwind Freight cut its release cycle from six weeks to two days

Northwind Freight runs the dispatch software behind about 1,400 trucks. For most of its history the engineering team shipped on a six-week train: code froze on a Friday, a manual regression pass ran over the following week, and a release engineer walked the build through four environments by hand. When a customer reported a routing bug, the fix waited for the next train.

The team adopted Harness Continuous Delivery in March 2025. The first three months went to prerequisites rather than the platform itself: splitting the dispatch monolith's database migrations out of the application deploy, adding health-check endpoints that meant something, and rewriting the regression suite so it ran in twelve minutes instead of nine hours. None of that work was visible to customers, and all of it had been deferred at least twice before.

Deployment counts tell the story. Northwind went from 8 production deploys in Q1 2025 to 312 in Q1 2026. Median lead time from merge to production dropped from 41 days to 3.5 hours. Change failure rate rose slightly, from 4% to 6.5%, but mean time to restore fell from 19 hours to 22 minutes, because a rollback is now a single pipeline stage instead of a war room. The team treats the higher failure rate as a fair trade at that recovery speed.

"We stopped treating deploys as events," says Priya Ramanathan, Northwind's director of platform engineering. "The scary part was never the tooling. It was admitting how much of our process existed because we didn't trust our tests. Once the suite ran in twelve minutes, half the ceremony had no argument left for it."

One service still sits behind a manual approval gate: the dispatch scheduler. Northwind expects to remove it once canary analysis covers the scheduler's latency budget.
