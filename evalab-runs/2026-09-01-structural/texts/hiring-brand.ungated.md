**How we build**

Small teams — usually three or four people, one of whom owns the thing end to end, design through the 2am page.

There's no separate QA org, and we're not going to hire one. If you write it, you test it, and you get woken up when it breaks. That sounds harsh until you notice what it buys: nobody can hand you a spec and walk away, and nobody can hand you a mess and call it done.

Code review is mandatory and fast. Median time to first comment last quarter was 41 minutes. We review for correctness, and for whether the next person will understand the code in a year. We don't review for style — the formatter already did that.

Deploys go out on demand, roughly 30 times a week. No release train, no change advisory board, no Thursday freeze. Rollback is one command and finishes in under a minute, which is the real reason we can move this way.

We write things down. Design docs before big changes, postmortems after outages, both readable by anyone in the company — including the ones where the author is the person who made the expensive mistake. Blame is boring. Causes are interesting.

Two things we're bad at, so you know going in. Onboarding docs lag the code by about a quarter. And we over-index on hiring people who enjoy ambiguity, which means if you want a clear ladder and a tightly defined scope, you will be frustrated here.

---

Every number is a placeholder — swap in your real review latency, deploy count, and rollback time, or cut the sentence. Fake specifics read worse than no specifics.
