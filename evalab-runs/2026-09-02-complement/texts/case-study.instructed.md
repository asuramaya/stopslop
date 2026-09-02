Northwind Logistics ships freight software to about 400 carrier customers. Two years ago, releases went out every six weeks, on a Saturday, with a four-person bridge call and a rollback plan nobody had rehearsed.

The team moved to a continuous delivery platform in March 2024. The migration took eleven weeks, most of it spent on things that had nothing to do with the platform: splitting a shared test database, retiring a build server that only one engineer knew how to restart, and writing the first real integration suite the codebase had ever had.

Deploy frequency went from roughly 8 releases a year to 30 to 40 a week. Median lead time from merge to production dropped from 19 days to 90 minutes. Change failure rate rose slightly at first, from 12% to 15%, then settled at 7% once the team started routing every change through a canary stage that holds new code at 5% of traffic for ten minutes.

"The batch size is the whole story," said Priya Raghunathan, who runs platform engineering there. "When a release contained six weeks of work, any failure meant bisecting six weeks. Now a bad deploy is one pull request and we know which one."

The cost is real. Northwind added an on-call rotation for the delivery pipeline itself and spends about 15% of one engineer's time keeping test flakiness under control. Raghunathan considers that a fair trade against the Saturday bridge calls.

The company is now extending the same pipeline to its two on-premise customers, which is harder, and expects that work to run through mid-2026.
