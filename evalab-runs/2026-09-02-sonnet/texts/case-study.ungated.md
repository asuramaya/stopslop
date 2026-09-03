**Case Study: Meridian Freight cuts release cycles from six weeks to same-day**

Meridian Freight runs dispatch and tracking software for about 200 regional trucking fleets. Through 2023, releases went out every six weeks. Each one required a two-day manual regression pass and a rollback plan the ops team dreaded using.

The engineering team adopted a continuous delivery platform in January 2024, wiring their existing test suite into an automated pipeline that runs on every merge to main. Deployments that once needed a change-review meeting and a Friday-morning window now happen automatically once tests pass.

"We used to batch fixes because shipping was expensive," said Priya Anand, Meridian's VP of Engineering. "Now a driver-app bug found in the morning is fixed by lunch."

The numbers back her up. Deploy frequency went from roughly 9 releases a year to over 300. Mean time to recover from a production incident dropped from four hours to eighteen minutes, since a bad change can be rolled back with one command instead of a coordinated hotfix. Lead time for a code change — from commit to production — fell from 11 days to under 2 hours.

The rollout wasn't without friction. The team spent three weeks rewriting flaky integration tests that had been tolerated under the old cadence but blocked every merge under the new one. Anand counts that cleanup as a separate win: the test suite finally tells the truth about what's broken.

Meridian now runs canary deployments for its billing service and plans to extend the same pipeline to its mobile driver app by the end of the year.
