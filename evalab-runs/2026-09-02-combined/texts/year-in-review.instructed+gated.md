# Platform engineering in 2026

We started January with a deploy pipeline that took 47 minutes and ended December at 9. That number is the one most of you will care about, so it goes first.

The rewrite of the build cache was the bulk of it. Priya and Tomas spent most of Q2 on the dependency graph, and the work was ugly — three separate attempts before we landed on content-addressed artifacts. The second attempt shipped, broke incremental builds for four days in June, and got rolled back. We wrote that up in the postmortem rather than quietly moving on, and the third attempt reused about half its code. Roughly a quarter of the year went into a thing that, from the outside, looks like one config change.

Incident count went from 31 to 14. Most of the drop came from one change: we stopped letting services page on-call for anything that a retry would have fixed within thirty seconds. That felt like cheating when Dan proposed it. It wasn't.

Things we said we'd do and didn't: the multi-region failover story is still a design doc. The observability migration is 60% done and stalled on the two legacy Java services nobody wants to touch. Both slide to 2027.

Headcount went from 9 to 12. Onboarding time for the three new engineers averaged 11 days to first production commit, down from the 20-odd days it took the previous cohort, mostly because Sam rewrote the local dev setup into a single command.

Next year the focus is failover. Details in January.
