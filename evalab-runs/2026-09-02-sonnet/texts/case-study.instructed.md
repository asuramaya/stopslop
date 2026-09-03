Meridian Freight ran its release process on a spreadsheet. Every deploy meant a Slack thread, a manual checklist, and someone on call in case the database migration went sideways. The engineering team shipped once every two weeks, and even that cadence slipped when the checklist owner was out.

They moved their deploy pipeline onto Harness CD in January 2026. The platform runs automated canary checks against a staging replica before any change reaches production traffic, and it rolls back on its own when error rates cross a threshold. That removed the two steps that used to require a human: watching dashboards after a push and deciding whether to revert.

Six months in, Meridian deploys 40 times a week, up from roughly twice a month. Lead time from merged pull request to production dropped from four days to under two hours. The team attributes most of the gain to smaller batch sizes: because deploys no longer require a scheduled window, engineers ship each change as it's ready instead of bundling a sprint's worth of work into one release.

"We used to treat deployment as an event," said Priya Raman, Meridian's director of engineering. "Now it's just what happens after a PR merges."

The change also affected incident response. Because each deploy carries fewer changes, rollbacks are faster to diagnose — the team can usually point to the single commit responsible within minutes rather than combing through a two-week batch.

Meridian's next step is extending the same pipeline to its data platform team, which still deploys on a weekly schedule.
