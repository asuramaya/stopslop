**Meridian Freight cuts release time from 19 days to 41 minutes**

Meridian Freight builds load-matching software for regional trucking dispatchers. Until March 2024, its 22 engineers shipped once every three weeks. Each release consumed a Thursday night and half of Friday. Priya Raghunathan, who ran the platform group, kept a spreadsheet of the manual steps. It had 47 rows.

Her team adopted Cadence that April. The first month went into instrumenting tests that had lived on one engineer's laptop for two years. Raghunathan then wired the pipeline to their staging cluster and let it promote to production behind a flag once smoke tests passed.

By August, the team deployed 31 times a week. The Thursday night ritual ended, and the two engineers who had owned release duty went back to writing features.

Raghunathan tracks three numbers. Mean time from merge to production fell from 19 days to 41 minutes. Rollbacks climbed from 2 a quarter to 9, which she counts as an improvement, since a rollback now costs four minutes instead of an evening. Customer-reported defects dropped 34 percent across two quarters.

The migration stalled twice. Flaky integration tests blocked the pipeline for six weeks, until Devin Okonjo rewrote the fixture setup and pinned the container versions. The on-call rotation also had to learn a new alerting path, and two pages went unanswered in June before Raghunathan fixed the routing.

She would run the same sequence again, with one change: fix the tests before touching the pipeline. Her spreadsheet is down to four rows, and she deletes one whenever Okonjo automates it.
