Subject line: a quarter of engineering time for technical debt

Our deploy failure rate has climbed for three straight quarters, and the last two incident reviews named the same root cause: code paths nobody wants to touch. We are asking for one engineering quarter, split across the team, to pay down the debt driving both.

Three areas account for most of the risk. The billing service's retry logic caused four production incidents since January, each requiring a manual database fix. The test suite for the API gateway takes 40 minutes to run. Engineers skip it locally and rely on CI, which pushes bugs later into the pipeline.

The auth module's config format changed twice with no migration path. We now maintain three parallel branches of logic to keep old integrations working.

Every sprint retro this year surfaced at least one of these issues. Estimates for new features in these areas run 2-3x normal because engineers work around the existing structure instead of through it.

We are asking for one quarter, not open-ended. We will fix the retry logic, cut test runtime to under 10 minutes, and collapse the auth branches to one.

We will track two numbers before and after: incident count tied to these systems, and estimate accuracy on tickets that touch them. If we don't do this now, the cost doesn't disappear. It shows up as slower features and more on-call pages next quarter. Spending the time deliberately now costs less than losing it in pieces later.
