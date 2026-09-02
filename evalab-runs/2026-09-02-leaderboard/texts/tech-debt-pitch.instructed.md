# Proposal: one quarter of engineering capacity for debt reduction

## What I'm asking for

Six engineers, one quarter, working only on the payments and identity services. No feature commitments from that group during the period.

## Why now

Our median PR in payments took 4.2 days to merge last quarter, against 1.1 days in the rest of the codebase. The gap is not people. It is that `payments-core` has 340 files with no test coverage, a build that takes 22 minutes, and three competing ways to construct a charge object. Every change requires reading all three.

We also had 11 production incidents last quarter. Seven traced back to the same class of problem: state written in one service, read by another that assumed a different schema version. We have patched each one individually. The patches are now part of the problem.

## What the quarter buys

Test coverage on the charge path first, because that is where the incidents cluster. Then collapse the three charge constructors into one, which removes roughly 6,000 lines. Then split the build so a payments change does not rebuild identity.

I expect the build to drop under 6 minutes and PR time in payments to come within a day of the rest of the codebase.

## What it costs

Two roadmap items slip: the merchant dashboard refresh and the second currency rollout. Both move to Q3. I've talked to Priya and she can defend that timeline with her customers if we commit to it now rather than in six weeks.

## The alternative

We keep paying the 3-day tax on every payments PR. That tax grows.
