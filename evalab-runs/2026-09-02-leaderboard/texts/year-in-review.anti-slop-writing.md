# 2025 in Review: What We Actually Shipped

March was the low point. Our deploy pipeline took 47 minutes and failed about one run in five, usually on a flaky integration test nobody owned. Priya spent two weeks tearing it apart and rebuilt the whole thing around parallel test shards. We're at 9 minutes now, with a failure rate under 2%. That change bought back roughly 40 engineer-hours a month, which we promptly spent on other things.

The billing migration went worse than planned. We said Q2. It landed in August. The Stripe webhook replay logic turned out to have three separate race conditions, and the third one only showed up under production load, so we found it the embarrassing way, at 2am on a Tuesday. Marcus wrote the postmortem. Worth reading if you missed it.

Good stuff too. We cut p99 latency on the search endpoint from 1.2s to 310ms by killing the N+1 query that had been sitting in that code path since 2023. Nobody noticed it for two years because the dataset was small. Then it wasn't.

Headcount went from 11 to 14. Onboarding still takes too long, about three weeks before a new hire ships anything real, and I don't have a fix for that yet. Ideas welcome.

Next year the big rock is the monolith split. I'm genuinely unsure whether we should do it. The arguments for are real, the arguments against are also real, and I've watched two other teams sink a year into this and come out slower.

We'll talk about it in January.
