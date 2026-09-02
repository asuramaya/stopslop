# Proposal: One quarter of engineering time for debt paydown

**To:** Leadership
**From:** Platform Engineering

I'm asking for one engineer-quarter — roughly 12 engineer-weeks across the four of us — to fix the parts of the codebase that are now slowing every feature we ship.

Here's what the debt costs us today. Our CI suite takes 47 minutes, and about one run in five fails for reasons unrelated to the change. Engineers rerun it, wait, context-switch, and come back. We measured two weeks of this in July: 31 hours of pure waiting time, plus the mistakes people make when they stop trusting a red build.

The billing service is the other problem. It has no test coverage below the API layer, so every change there goes out on manual QA. The last three billing releases each slipped a week. Two of them shipped bugs anyway.

What we'd do with the quarter:

- Split the CI suite and quarantine the flaky tests. Target: 12 minutes, under 2% unrelated failures.
- Write unit tests for billing's pricing and proration logic, the two areas that produced all three of last quarter's incidents.
- Delete the v1 API handlers. Nobody has called them since March, and they double the surface area of every auth change.

The cost is real: three features move from Q4 to Q1. I've listed which ones in the appendix, and I don't think any of them are load-bearing for the renewal cycle.

If we don't do this, the CI number keeps climbing. It was 31 minutes in January.
