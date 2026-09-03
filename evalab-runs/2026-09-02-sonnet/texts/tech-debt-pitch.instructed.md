Subject: Requesting one quarter of engineering time for technical debt

Our deploy frequency dropped from three times a week to once every ten days over the last two quarters. The cause isn't team size or process — it's the codebase. Three systems account for most of the drag: the billing service still runs on the pre-2024 event schema, the test suite takes 40 minutes and fails intermittently on unrelated code, and the auth module has no owner since the platform team reorg.

I'm asking for one engineer-quarter (roughly 3 people for one quarter, or the equivalent spread across the team) to address these three items:

1. Migrate billing off the legacy event schema. This removes the dual-write path that causes most of our production incidents in that service.
2. Fix the flaky tests and cut suite runtime to under 10 minutes. Engineers currently re-run CI two or three times per PR to get a clean signal.
3. Assign clear ownership to the auth module and document its current behavior. Two of the last four security review findings trace back to changes made without anyone who understood the full system.

Cost: roughly 3 engineer-months, paid from the quarter's existing roadmap capacity rather than as additional headcount.

Expected outcome: return to twice-weekly deploys and cut CI turnaround by more than half, based on the before-and-after numbers from the similar cleanup the payments team did in Q1.

I'd like 30 minutes on the roadmap planning agenda to walk through the specific tickets and get a decision before sprint planning starts.
