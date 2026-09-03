Subject: Proposal — one quarter of engineering time for technical debt

Team,

I'm asking for a quarter of dedicated engineering time to pay down technical debt in the core service layer.

Over the past year we've shipped features fast and pushed cleanup to "later." Later hasn't come. Three areas now cost us real time every sprint: the billing module still runs on the pre-migration data model, so every change there needs a manual reconciliation step; our test suite takes 40 minutes and flakes often enough that engineers routinely skip it before merging; and the auth service has two competing session-handling paths left over from the SSO rollout, which caused the login outage in June.

The cost of not fixing this is compounding. New feature work in billing now takes roughly 1.5x longer than equivalent work elsewhere, based on the last four sprint retros. Flaky tests erode confidence in CI, which means bugs reach production that CI should catch. And the duplicate auth paths are one bad deploy away from another outage.

The ask: one engineer-quarter, split across a four-person team for three weeks, or two engineers for six. Deliverables: complete the billing data migration, cut test suite runtime to under 15 minutes and fix the top flaky tests, and remove one of the two auth session paths.

This isn't a rewrite and it doesn't touch the roadmap features planned for Q4. It's scoped, it has a fixed end date, and each deliverable is independently shippable if priorities shift mid-quarter.

Happy to walk through the breakdown in our next planning meeting.
