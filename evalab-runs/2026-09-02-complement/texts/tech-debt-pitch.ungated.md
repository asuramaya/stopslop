## Proposal: One Quarter of Engineering Time for Debt Paydown

**To:** Leadership
**From:** Engineering
**Ask:** Dedicate Q1 engineering capacity to technical debt, with feature work paused except for committed customer obligations.

Here is the situation. Our median time from merged PR to production has gone from two days to nine over the past year. The cause isn't any one system — it's the accumulated cost of shortcuts we took deliberately, and correctly, to hit ship dates. Those shortcuts are now the reason estimates slip.

Three areas account for most of it:

The billing service has no test coverage below the API layer, so every change there ships on manual QA. That's roughly a week of engineer time per release.

The deploy pipeline runs on a build system two major versions out of support. When it breaks, three people can fix it.

We maintain two ORMs and two auth paths because a migration stalled in 2024. Every new endpoint requires a judgment call about which half of the codebase it lives in, and that call is frequently wrong.

What we'd deliver by end of quarter: billing under integration test, the pipeline migrated and documented, and the ORM migration finished. Nothing user-visible ships from this work.

That last sentence is the real cost, and I want to be direct about it — a quarter with no new features is a quarter competitors use. My argument is that we're already paying this cost, just spread thin and invisibly, in slipped estimates and firefighting. I'd rather pay it once, on purpose.

I'm happy to scope this down to six weeks if a full quarter is untenable. I'd want to talk through what we'd drop.
