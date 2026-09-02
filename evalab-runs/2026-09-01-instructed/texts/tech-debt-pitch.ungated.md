Here's a draft. The bracketed numbers are the ones you'll need to fill from your own tracking — a proposal like this lives or dies on whether the figures are real.

---

**To:** Engineering Leadership
**Re:** Dedicating Q[X] to technical debt
**From:** [Name]

I'm asking for one quarter of the team's capacity — no new feature commitments — to pay down accumulated technical debt.

The case is arithmetic, not aesthetic. Over the last two quarters, [N]% of our engineering hours went to unplanned work: production incidents, regressions, and fixes to fixes. Our median time from merge to deploy has gone from [X] to [Y] days, mostly because the test suite takes [Z] minutes and fails intermittently, so people rerun it rather than trust it. Two of our services can only be safely modified by one person each. That's a staffing risk we've been quietly absorbing.

Concretely, the quarter would cover: cutting CI time and removing flaky tests; retiring the [legacy component]; and adding integration coverage to the [X] payment path so changes there stop requiring manual verification.

What I expect afterward: unplanned work back under [N]%, deploys same-day, and no single-owner services.

I want to be straight about the cost. We would ship no roadmap features for three months, and [commitment A] and [commitment B] would slip to Q[X+1]. That's a real loss, and I'd rather name it than bury it in a slide.

The alternative isn't free either. We've been paying this down in fragments for a year, and the fragments haven't held. Each quarter we defer, the interest gets larger and the eventual bill gets less predictable.

Happy to walk through the numbers with anyone who wants the detail.

---

Roughly 255 words. Want me to save it to a file, or adjust the tone — more deferential, or harder-edged?
