# Platform engineering team charter

## Why we exist

Product teams at this company spend too much of their week on work that is not their product: wiring up CI, chasing a broken deploy, guessing which of four logging setups is current. We own that work so they don't have to. Our customers are the engineers here, and our product is the path they take from a merged pull request to running code.

## What we own

Build and CI infrastructure, deployment pipelines, environment provisioning, observability defaults, and the internal documentation for all of it. We own the paved road end to end — if a team steps off it, that is a signal about the road, not about the team.

## How we work

We take requests, but we prefer patterns. A one-off fix for one team is a stopgap; if three teams ask for the same thing, it becomes a supported capability with an owner and a runbook. We publish what we are working on and what we have declined, and why.

We do not gatekeep. Teams can deploy without our approval and can run infrastructure we don't support, provided they carry the pager for it.

## What we measure

Time from merge to production, change failure rate, and the count of teams on the paved road versus off it. We will report these monthly, starting with whatever baseline we can gather in our first six weeks, even if it is rough.

## What we are not

Not a ticket queue, not a rename of the old ops team, and not the group that says no. If we become any of those, this charter has failed and should be rewritten.
