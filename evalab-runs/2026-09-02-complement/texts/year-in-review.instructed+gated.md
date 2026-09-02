# The year in the platform team

We started January with a deploy pipeline that took 47 minutes and ended December with one that takes 9. That is the number I'd point at if someone asked what we did all year, though it undersells the boring parts that got us there.

The migration off the monolith's job runner was the big one. It took from March to August, three weeks longer than we told everyone it would, mostly because the retry semantics in the old system were undocumented and load-bearing. Two incidents came out of that — the April duplicate-charge bug and the June queue stall. Both are written up in the incident log, and both changed how we do cutovers: we now dual-write for a full billing cycle before we cut reads over.

Kenji's work on the schema registry deserves more attention than it got internally. Sixteen services now validate events at publish time instead of discovering malformed payloads in a consumer three hops downstream. Producer-side rejections are up, which is the point.

We hired four people and lost one. Onboarding time to first merged PR dropped from eleven days to four after Priya rewrote the local dev setup, which had been quietly broken on Apple silicon since 2024.

Things we said we'd do and didn't: the tracing rollout stalled at 40% of services, and the on-call rotation is still six people deep when it should be ten. Both carry into next year.

Next year's shape is less migration, more paying down what the migration left behind.
