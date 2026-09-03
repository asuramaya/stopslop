Subject: Proposal — Dedicate Q4 Engineering Capacity to Technical Debt

I'm asking for one quarter of engineering time, spread across the team, to pay down technical debt that slows every roadmap item we ship.

Feature velocity dropped over the last two quarters even though headcount stayed flat. Code reviews take longer because the codebase carries inconsistent patterns from three different architectural eras. Onboarding a new engineer takes six weeks instead of two, mostly spent explaining workarounds that exist for reasons nobody remembers. Our incident count is climbing, and a growing share traces back to the same fragile modules: the payments retry logic and the auth session layer.

We have tried squeezing debt paydown into sprint margins. That has not worked. It gets deprioritized every time, and the interest keeps compounding.

Here is what we will do with the quarter:

- Refactor the payments retry logic and auth session layer, the two areas responsible for most recent incidents
- Consolidate three overlapping internal libraries into one
- Raise test coverage on the checkout flow, our highest-risk, lowest-coverage path
- Delete dead code and unused feature flags — a smaller effort, but it removes a lot of noise for reviewers

In return, leadership gets faster feature delivery starting in Q1, fewer production incidents, and shorter onboarding time for new hires. We will also come out with clearer ownership boundaries, which cuts the cross-team coordination overhead we absorb on nearly every launch.

I am glad to walk through specifics or adjust scope if a full quarter is not feasible.
