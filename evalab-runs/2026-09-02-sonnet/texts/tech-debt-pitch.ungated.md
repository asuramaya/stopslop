**Subject: Proposal — One Quarter for Technical Debt**

Our velocity has slowed over the last two quarters, and it's not from lack of effort. Every feature now touches code nobody fully understands, tests that take too long to trust, and dependencies three major versions behind. I'm asking for one quarter where a dedicated slice of engineering time goes toward paying this down instead of shipping new features.

Specifically, I'd like to commit 25% of the team's capacity — roughly two engineers' worth of time — to:

- Upgrading our core dependencies before the gap becomes a security liability
- Breaking apart the billing service, which has become the single point of failure for three unrelated teams
- Rebuilding our test suite so CI runs in minutes, not the current 40
- Deleting the dead code paths we keep working around instead of removing

None of this ships a customer-facing feature. All of it determines how fast we can ship the next ten.

The cost of doing nothing is compounding: our last two incidents traced back to the same legacy billing code, and onboarding a new engineer now takes twice as long as it did a year ago. That's not a one-time cost — it repeats every sprint.

I'm not asking for an open-ended cleanup effort. I want a scoped list, a named owner for each item, and a checkpoint at six weeks so we can cut anything that isn't earning its time. If leadership prefers a smaller pilot first, I'd suggest starting with the billing service alone as a four-week trial.

Happy to walk through the specifics in person.
