**We Split the Monolith. Here's the Bill.**

Eighteen months ago our Rails app was 400,000 lines and one deploy button. Today it's fourteen services, and I want to be honest about what that cost.

The talk walks through the decomposition we actually did: pulling billing out first because it had the cleanest data boundary, then payments, then the long tail of things nobody wanted to own. I'll show the seams we cut along, the two we cut wrong, and the rollback that took nine hours because a "stateless" service turned out to hold a cache nothing else knew about.

Some numbers. Deploy frequency went from weekly to roughly forty times a day. p99 latency on checkout got worse — 210 ms to 340 ms — and stayed worse for four months while we learned to trace across process boundaries. On-call pages tripled before they dropped below where they started.

If you're weighing this migration, you probably want to know whether the pain has a shape you can plan around. Mostly it does. I'll give you the sequencing that worked, the tooling we should have built in month one instead of month eleven, and three cases where the right answer was to leave the monolith alone.
