**Technical debt, this month**

Nobody on this team set out to write bad code. We wrote code on a deadline, and then the deadline moved, and then we shipped something else. That's how the billing service ended up with three ways to compute a proration.

This month we're looking at the interest payments. In August, 41% of our incident time traced back to two files: `legacy_sync.py` and the notification dispatcher. Both were flagged in code review, in 2023, by people who no longer work here.

Inside you'll find four pieces. Priya walks through the auth rewrite: what she kept, what she deleted, and the two weeks she lost to a config flag nobody could explain. Marcus makes the case that our test suite is itself debt, since 300 of the 1,800 tests have been skipped for over a year. Dana has numbers on how long a "temporary" workaround survives here (median: 14 months). And we're publishing the debt register we've been keeping in a private doc since March, so you can see what we already know is broken.

We're not asking for a debt sprint. We're asking you to pick one thing in your area, write down what it costs, and put it on the register.
