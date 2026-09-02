Passes the slopwatch gate clean. Here's the post — the specifics are placeholders, so swap in your real numbers, names, and quarters.

---

**2025 in review: the boring year we needed**

Nobody asked for a rewrite this year, and we didn't do one. That's the headline.

We spent Q1 paying down the deploy pipeline. Builds went from 22 minutes to just under 6, mostly by killing the monolithic test job and letting the four suites run on their own. The dull part, untangling fixtures that three teams shared, took nine weeks. Worth it.

In April we moved auth onto the shared identity service. Two incidents came out of that, both ours, both paging on-call at hours nobody should be awake. We wrote them up honestly. The postmortem on the second one is the best internal doc we produced all year; go read it if you haven't.

Then the search rewrite, which we scoped down twice and shipped in September. p95 latency sits at 180 ms now, down from 1.4 s. Support tickets about "search is broken" dropped by roughly two thirds.

Things that didn't work: the feature-flag cleanup sprint (we removed 40 flags and added 55), and our second attempt at a shared component library, which stalled in review for four months before we archived it.

Headcount went from 9 to 12. Priya and Marcus joined the platform side; Dan moved to infra.

Next year: fewer initiatives, finished. We have three on the board, and we aren't adding a fourth until one of them ships.

---

Two things you may want to adjust: the "things that didn't work" section is the part that makes the post worth reading, so keep it even if it gets softened elsewhere — and if the incidents were more painful than one line suggests, give them a paragraph of their own instead.
