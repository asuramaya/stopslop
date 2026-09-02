**Proposal: 25 percent of Q4 engineering capacity for debt paydown**

We lost 41 engineer-days to unplanned work last quarter. I traced 34 of them to four sources: the billing service's shared mutable config, the 2019 auth middleware nobody owns, a test suite that runs 52 minutes and fails at random on 6 percent of runs, and a deploy script that needs someone watching it for 20 minutes.

I am asking for one quarter of one engineer-equivalent, spread across the team as a standing Wednesday, through the end of Q4.

The plan: Ana and Priya rewrite the billing config loader and delete the two paths that read it out of order. Marcus takes ownership of the auth middleware and cuts it to the three endpoints that still call it. I split the test suite into unit and integration tiers and quarantine the eight flaky specs, which brings CI under 12 minutes. Sam automates the deploy checks we do by hand.

We keep the Q4 roadmap. The two features Sales committed to for November ship on schedule, because the debt work runs in parallel and touches different services.

What we get back: I expect unplanned work to drop under 15 engineer-days in Q1, and the CI change alone returns about 90 engineer-hours per quarter in waiting.

The risk of waiting: the auth middleware has one person who understands it, and Marcus's notice period is two weeks.

I will report progress against these four items at each biweekly review, with the unplanned-work number attached. If the trend flattens by week six, we stop and give the capacity back.
