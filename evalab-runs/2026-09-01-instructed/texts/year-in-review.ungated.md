**2026: the year we stopped shipping the roadmap**

Twelve months ago we had a roadmap with fourteen items on it. We shipped nine. Two of the five we dropped turned out to be the ones customers actually wrote in about, which is a lesson I keep re-learning.

Highlights, in the order they mattered:

The migration off [old system] finally landed in March. Eight weeks late, and worth every week — p99 on the checkout path went from 1.4s to 310ms, and the pager stopped going off at 3am on Sundays.

[Name] rewrote the deploy pipeline during what was supposed to be a quiet quarter. Deploys take 6 minutes now instead of 40. Nobody asked for this. Everybody uses it.

We also broke production twice. The June incident was mine: a config change I reviewed too fast on a Friday afternoon. We wrote it up honestly, added the guardrail, moved on. The postmortems are in [link] and they're better reading than this post.

What I'd change: too much of Q3 went into planning meetings about Q4. Estimates got worse the more we talked about them. Next year we're committing two weeks out and refusing to pretend about anything past that.

Headcount went from 6 to 9. Onboarding is still a wiki page and a prayer, which is the first thing we fix in January.

Thanks for a good year. See you Monday.

---

~245 words. Swap the bracketed bits for your real system, name, and link — the numbers are placeholders too, and the post only works if they're yours.
